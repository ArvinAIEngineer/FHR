import os
import time
import aiohttp
from threading import Timer
from typing import List, Dict, Any, Optional
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from utils.logger import get_logger

os.environ['NO_PROXY'] = '10.254.115.17'

class ConversationManager:
    def __init__(self, orchestrator):
        """
        Initialize the conversation manager.

        Args:
            orchestrator: The orchestrator instance with checkpointer access
        """
        self.orchestrator = orchestrator
        self.active_conversations = {}  # Stores thread_id -> last_access_time
        self.expiry_time = 3600  # 1 hour in seconds
        self.logger = get_logger()
        self.start_cleanup_timer()
        self.logger.info("Conversation manager initialized")

    def is_conversation_active(self, thread_id: str) -> bool:
        """
        Check if a conversation is already loaded and active.

        Args:
            thread_id: The thread identifier

        Returns:
            bool: True if conversation is active, False otherwise
        """
        is_active = thread_id in self.active_conversations
        if is_active:
            # Update timestamp if conversation exists
            self.update_conversation_timestamp(thread_id)
        return is_active

    def update_conversation_timestamp(self, thread_id: str) -> None:
        """
        Update the last access timestamp for a conversation.

        Args:
            thread_id: The thread identifier
        """
        self.active_conversations[thread_id] = time.time()
        self.logger.debug(f"Updated timestamp for thread {thread_id}")

    async def load_conversation_history(self, thread_id: str, api_config: Dict[str, Any]) -> List[BaseMessage]:
        """
        Load conversation history from API and track it in active conversations.

        Args:
            thread_id: The thread identifier
            api_config: API configuration dictionary with base_url, headers, and timeout

        Returns:
            List[BaseMessage]: The conversation history messages
        """
        # add timestamp for the new conversation
        self.update_conversation_timestamp(thread_id)

        # Load conversation history from API
        chat_history = await self.load_conversation_history_from_api(thread_id, api_config)
        return chat_history

    async def load_conversation_history_from_api(self, thread_id: str, api_config: Dict[str, Any]) -> List[BaseMessage]:
        """
        Load conversation history from API using the GetConversationDetails endpoint.

        Args:
            thread_id: The thread identifier
            api_config: Dictionary containing API configuration
                       {
                           "base_url": "https://api.example.com",
                           "headers": {"Authorization": "Bearer token"},
                           "timeout": 30
                       }

        Returns:
            List of BaseMessage objects representing the conversation history
        """
        chat_history = []

        if not api_config:
            self.logger.info("No API config provided for conversation history")
            return chat_history

        try:
            base_url = api_config.get("base_url", "").rstrip('/')
            headers = api_config.get("headers", {})
            timeout = api_config.get("timeout", 30)

            # Construct URL with query parameter
            url = f"{base_url}/api/Conversations/GetConversationDetails"
            params = {"conversationId": thread_id}

            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        conversation_data = await response.json()

                        # Handle the API response structure
                        if conversation_data.get('success', False):
                            data = conversation_data.get('data', {})
                            messages_data = data.get('messages', [])

                            # Convert API data to message objects
                            for msg in messages_data:
                                human_message = msg.get('humanMessage', '')
                                ai_message = msg.get('aiMessage', '')
                                
                                # Parse timestamps for ordering
                                human_created_on = msg.get('humanCreatedOn')
                                ai_created_on = msg.get('aiCreatedOn')
                                
                                # Create a list to hold this message pair with timestamps
                                message_pairs = []
                                
                                # Add human message if it exists
                                if human_message:
                                    human_timestamp = None
                                    if human_created_on:
                                        try:
                                            from datetime import datetime
                                            human_timestamp = datetime.fromisoformat(human_created_on.replace('Z', '+00:00'))
                                        except ValueError:
                                            pass
                                    message_pairs.append((HumanMessage(content=human_message), human_timestamp))
                                
                                # Add AI message if it exists
                                if ai_message:
                                    ai_timestamp = None
                                    if ai_created_on:
                                        try:
                                            from datetime import datetime
                                            ai_timestamp = datetime.fromisoformat(ai_created_on.replace('Z', '+00:00'))
                                        except ValueError:
                                            pass
                                    message_pairs.append((AIMessage(content=ai_message), ai_timestamp))
                                
                                # Sort by timestamp and add to chat history
                                message_pairs.sort(key=lambda x: x[1] if x[1] is not None else datetime.min.replace(tzinfo=datetime.now().astimezone().tzinfo))
                                for message, _ in message_pairs:
                                    chat_history.append(message)

                            self.logger.info(f"Loaded {len(chat_history)} messages from conversation {thread_id}")
                        else:
                            error_msg = conversation_data.get('message', 'Unknown error')
                            self.logger.warning(f"API returned error for conversation {thread_id}: {error_msg}")

                    elif response.status == 404:
                        self.logger.info(f"No conversation found with ID {thread_id}")
                        try:
                            error_data = await response.json()
                            error_msg = error_data.get('message', 'Conversation not found')
                            self.logger.info(f"404 Error: {error_msg}")
                        except:
                            self.logger.info("404 Error: Conversation not found")
                    else:
                        self.logger.warning(f"API returned status {response.status} for conversation {thread_id}")
                        error_text = await response.text()
                        self.logger.warning(f"Error response: {error_text}")

        except aiohttp.ClientError as e:
            self.logger.error(f"HTTP error loading conversation history for ID {thread_id}: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error loading conversation history from API for ID {thread_id}: {str(e)}")

        return chat_history

    def get_thread_history(self, thread_id: str) -> List:
        """
        Get the current conversation history for a thread from the checkpointer.

        Args:
            thread_id: The thread ID to get history for

        Returns:
            List of messages in the thread
        """
        try:
            # Get the current state from checkpointer
            config = {"configurable": {"thread_id": thread_id}}

            # Get the latest checkpoint for this thread
            checkpoint = self.orchestrator.checkpointer.get(config)

            if checkpoint and "messages" in checkpoint["channel_values"]:
                return checkpoint["channel_values"]["messages"]
            else:
                return []

        except Exception as e:
            self.logger.error(f"Error getting thread history: {str(e)}")
            return []

    def clear_inactive_conversations(self) -> None:
        """
        Clear conversations that have been inactive for more than the expiry time.
        """
        current_time = time.time()
        inactive_ids = []

        # Find inactive conversation IDs
        for thread_id, last_access in list(self.active_conversations.items()):
            if current_time - last_access > self.expiry_time:
                inactive_ids.append(thread_id)

        # Clear inactive conversations
        for thread_id in inactive_ids:
            success = self.clear_thread_history(thread_id)
            if success:
                self.logger.info(f"Cleared inactive thread {thread_id}")
            else:
                self.logger.warning(f"Failed to clear inactive thread {thread_id}")

        # Log how many conversations were cleared
        if inactive_ids:
            self.logger.info(f"Cleared {len(inactive_ids)} inactive threads")

    def clear_thread_history(self, thread_id: str) -> bool:
        """
        Clear the thread history for the given thread ID.
        Uses orchestrator's clear_thread_history method to delete from checkpointer.

        Args:
            thread_id: The thread identifier to clear

        Returns:
            bool: True if successfully cleared, False otherwise
        """
        # Remove from active conversations list
        if thread_id in self.active_conversations:
            del self.active_conversations[thread_id]

        try:
            self.orchestrator.checkpointer.delete_thread(thread_id)
            self.logger.info(f"Thread {thread_id} history clear requested")
            return True

        except Exception as e:
            self.logger.error(f"Error clearing thread history: {str(e)}")
            return False

    def start_cleanup_timer(self) -> None:
        """
        Start a timer to periodically clean up inactive conversations.
        """
        # Run cleanup every 15 minutes
        cleanup_interval = 900  # 15 minutes in seconds


        def cleanup_and_reschedule():
            self.clear_inactive_conversations()
            self.start_cleanup_timer()

        # Schedule the next cleanup
        timer = Timer(cleanup_interval, cleanup_and_reschedule)
        timer.daemon = True  # Allow the timer to be terminated when the program exits
        timer.start()
        self.logger.debug(f"Started cleanup timer with interval {cleanup_interval} seconds")