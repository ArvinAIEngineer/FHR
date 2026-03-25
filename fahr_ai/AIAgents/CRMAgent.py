import json
import os
import sys
from langchain_openai import ChatOpenAI
import yaml
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Literal, TypedDict, Optional
from dataclasses import dataclass
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Add the current directory to sys.path
sys.path.append("./")
from api.crm_handler import CRMTicketHandler
from langgraph.graph import StateGraph
from langchain.schema import HumanMessage
from api.mock_crm_client import MockCRMClient
from utils.logger import get_logger
from AIAgents.base_agent import GraphState
import logging
os.environ['NO_PROXY'] = '10.254.115.17, 10.254.140.69'

@dataclass
class CachedTicketData:
    """Cached ticket data with timestamp"""
    data: Dict[str, Any]
    timestamp: datetime
    summary: Optional[str] = None

class CRMResponse(TypedDict):
    """CRMResponse defines the structure of the response from the CRM agent."""
    status: Literal["MATCH", "NO_MATCH"]
    answer: str

class CRMAgent:
    def __init__(self, crm_url: str, config_path: str, llm=None, 
                 cache_ttl_minutes: int = 30, max_cache_size: int = 1000):
        self.crm_ticket_handler = CRMTicketHandler(crm_url)
        self.llm = llm
        self.logger = get_logger()
        
        # Caching configuration
        self.cache_ttl = timedelta(minutes=cache_ttl_minutes)
        self.max_cache_size = max_cache_size
        self.ticket_cache: Dict[str, CachedTicketData] = {}
        self.summary_cache: Dict[str, tuple] = {}  # (summary, timestamp)
        
        # Thread pool for parallel processing
        self.executor = ThreadPoolExecutor(max_workers=3)

        self.logger.info(f"Loading config from {config_path}")
        with open(config_path, 'r', encoding="utf-8") as file:
            self.config = yaml.safe_load(file)
            self.prompt_template = self.config['crmAgent_prompt']

        self.mock_crm_client = MockCRMClient()
        
        # Pre-compile common patterns for faster processing
        self._setup_optimizations()

    def _setup_optimizations(self):
        """Setup optimizations like connection pooling, pre-compiled patterns"""
        # Pre-warm the LLM if possible
        if hasattr(self.llm, 'warm_up'):
            self.llm.warm_up()

    def _get_cache_key(self, username: str, query_hash: str = "") -> str:
        """Generate cache key for user tickets"""
        return f"{username}_{query_hash}" if query_hash else username

    def _is_cache_valid(self, cached_data: CachedTicketData) -> bool:
        """Check if cached data is still valid"""
        return datetime.now() - cached_data.timestamp < self.cache_ttl

    def _cleanup_cache(self):
        """Remove expired entries and enforce size limits"""
        now = datetime.now()
        
        # Remove expired entries
        expired_keys = [
            key for key, data in self.ticket_cache.items()
            if now - data.timestamp >= self.cache_ttl
        ]
        for key in expired_keys:
            del self.ticket_cache[key]
        
        # Remove oldest entries if cache is too large
        if len(self.ticket_cache) > self.max_cache_size:
            sorted_items = sorted(
                self.ticket_cache.items(),
                key=lambda x: x[1].timestamp
            )
            items_to_remove = len(self.ticket_cache) - self.max_cache_size
            for key, _ in sorted_items[:items_to_remove]:
                del self.ticket_cache[key]

    async def _get_cached_or_fetch_tickets(self, username: str, runtime_config: dict) -> Dict[str, Any]:
        """Get tickets from cache or fetch from CRM"""
        cache_key = self._get_cache_key(username)
        
        # Check cache first
        if cache_key in self.ticket_cache:
            cached_data = self.ticket_cache[cache_key]
            if self._is_cache_valid(cached_data):
                self.logger.info(f"Using cached ticket data for {username}")
                return cached_data.data
            else:
                # Remove expired entry
                del self.ticket_cache[cache_key]
        
        # Fetch fresh data
        self.logger.info(f"Fetching fresh ticket data for {username}")
        if username == 'FAHR506849':
            ticket_data = mock_ticket_data()
        else:
            ticket_data = await self.crm_ticket_handler.get_ticket_data(runtime_config)
        
        # Cache the data
        self.ticket_cache[cache_key] = CachedTicketData(
            data=ticket_data,
            timestamp=datetime.now()
        )
        
        # Cleanup cache periodically
        if len(self.ticket_cache) % 10 == 0:  # Every 10 additions
            self._cleanup_cache()
        
        return ticket_data

    def _generate_summary_hash(self, ticket_data: Dict[str, Any]) -> str:
        """Generate hash for ticket data to check if summary needs updating"""
        # Create a hash based on ticket content
        content = json.dumps(ticket_data, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()

    async def _get_cached_or_generate_summary(self, ticket_data: Dict[str, Any], username: str) -> str:
        """Get summary from cache or generate new one"""
        data_hash = self._generate_summary_hash(ticket_data)
        cache_key = f"{username}_{data_hash}"
        
        # Check summary cache
        if cache_key in self.summary_cache:
            summary, timestamp = self.summary_cache[cache_key]
            if datetime.now() - timestamp < self.cache_ttl:
                self.logger.info(f"Using cached summary for {username}")
                return summary
        
        # Generate new summary
        self.logger.info(f"Generating new summary for {username}")
        summary = await self._summarize_tickets_with_llm_optimized(ticket_data)
        
        # Cache the summary
        self.summary_cache[cache_key] = (summary, datetime.now())
        
        return summary

    async def _summarize_tickets_with_llm_optimized(self, data: Dict[str, Any]) -> str:
        """Optimized ticket summarization with parallel processing"""
        open_tickets = data.get("open", [])
        closed_tickets = data.get("closed", [])
        
        if not open_tickets and not closed_tickets:
            return "No tickets found for user."
        
        # Process open tickets in parallel
        open_summaries = []
        if open_tickets:
            # Create tasks for parallel processing
            tasks = []
            for ticket in open_tickets:
                if not ticket.get("comments"):
                    continue
                task = self._summarize_single_ticket(ticket)
                tasks.append(task)
            
            if tasks:
                # Process up to 3 tickets concurrently
                batch_size = 3
                for i in range(0, len(tasks), batch_size):
                    batch = tasks[i:i + batch_size]
                    results = await asyncio.gather(*batch)
                    open_summaries.extend(results)
        
        # Process closed tickets (simpler, no LLM needed)
        closed_summaries = [
            f"Ticket #{t['id']}: Closed - {t.get('resolution', 'No resolution provided.')}"
            for t in closed_tickets
        ]
        
        return "\n".join(open_summaries + closed_summaries)

    async def _summarize_single_ticket(self, ticket: Dict[str, Any]) -> str:
        """Summarize a single ticket"""
        crm_service_name = ticket.get("crm_service_name", "Unknown Service")
        crm_group_name = ticket.get("crm_group_name", "Unknown Group")
        request_details = ticket.get("request_details", "No details provided.")
        comments = ticket.get("comments", [])
        
        # Optimize prompt to be more concise
        prompt = (
            f"Summarize ticket #{ticket['id']} concisely:\n"
            f"Service: {crm_service_name} | Group: {crm_group_name}\n"
            f"Details: {request_details}\n"
            f"Comments: {'; '.join(comments[:3])}\n"  # Limit to first 3 comments
            f"Provide a brief summary only."
        )
        
        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            return f"Open Ticket #{ticket['id']}: {response.content}"
        except Exception as e:
            self.logger.error(f"Error summarizing ticket {ticket['id']}: {e}")
            return f"Open Ticket #{ticket['id']}: Error generating summary"

    def _extract_user_query_optimized(self, state: GraphState) -> str:
        """Optimized user query extraction"""
        # Cache the last human message to avoid repeated searches
        if hasattr(self, '_last_query_cache'):
            return self._last_query_cache
        
        for msg in reversed(state['messages']):
            if isinstance(msg, HumanMessage):
                self._last_query_cache = msg.content
                return msg.content
        
        return ""

    async def run(self, state: GraphState, runtime_config: dict) -> GraphState:
        """ Run the CRM agent to fetch and summarize tickets for a user with caching and parallel processing.
        Args:
            state (GraphState): The current state of the graph.
            runtime_config (dict): Configuration for the runtime environment.
        Returns:
            GraphState: Updated state with ticket summaries and CRM responses.
        """
        thread_id = int(runtime_config["configurable"]["thread_id"])
        self.logger = get_logger(thread_id)
        self.logger.setLevel(logging.INFO)
        start_time = time.time()
        self.logger.info("Running CRM Agent")
        username = runtime_config["configurable"]["userInfo"].get("person_id", "")
        if not username:
            self.logger.warning("User name not provided in context")
            state["ticket_summary"] = "No user name provided."
            return state

        # Extract user query (optimized)
        user_query = self._extract_user_query_optimized(state)
        self.logger.info(f'User query: {user_query}')

        try:
            # Get tickets (cached or fresh)
            ticket_data = await self._get_cached_or_fetch_tickets(username, runtime_config)
            
            # Get summary (cached or generate)
            summary = await self._get_cached_or_generate_summary(ticket_data, username)
            
            if not summary or summary == "No tickets found for user.":
                self.logger.warning(f"No tickets found for username: {username}")
                state["error"] = "No tickets found for the user."
                state["route"] = "chat_agent"
                return state
            
            state["ticket_summary"] = summary
            
            # Generate CRM response
            formatted_prompt = self.prompt_template.format(
                user_question=user_query,
                summary_text=summary
            )
            
            messages = [{"role": "system", "content": formatted_prompt}]
            response = await self.llm.with_structured_output(CRMResponse).ainvoke(messages)
            state["crm_response"] = response
            
            elapsed_time = time.time() - start_time
            self.logger.info(f"CRM Agent completed in {elapsed_time:.2f} seconds")
            self.logger.info(f"CRM Response: {response}")
            
            return state
            
        except Exception as e:
            self.logger.error(f"Error in CRM Agent: {e}")
            state["error"] = f"Error processing request: {str(e)}"
            return state

    def clear_cache(self):
        """Clear all caches"""
        self.ticket_cache.clear()
        self.summary_cache.clear()
        if hasattr(self, '_last_query_cache'):
            delattr(self, '_last_query_cache')
        self.logger.info("Caches cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "ticket_cache_size": len(self.ticket_cache),
            "summary_cache_size": len(self.summary_cache),
            "cache_ttl_minutes": self.cache_ttl.total_seconds() / 60
        }

    # Keep the original methods for backward compatibility
    async def run_with_mock(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Original mock method - kept for backward compatibility"""
        username = state.get("username")
        if not username:
            state["error"] = "Missing username"
            return state

        tickets = self.mock_crm_client.fetch_all_tickets(username)
        open_tickets = {}
        closed_tickets = []

        for ticket in tickets:
            case_number = ticket["CRM_Case_Number"]
            status = ticket["StatusID"]

            if status.lower() == "assigned":
                comments = self.mock_crm_client.fetch_ticket_comments(case_number)
                comment_bodies = "\n".join([c["Body"] for c in comments])
                summary_prompt = f"Summarize the following comments:\n{comment_bodies}"
                summary = await self.llm.ainvoke(summary_prompt)
                open_tickets[case_number] = {
                    "summary": summary.content,
                    "details": ticket,
                    "comments": comments
                }
            else:
                closed_tickets.append(ticket)

        state["open_ticket_summaries"] = open_tickets
        state["closed_ticket_info"] = closed_tickets
        return state


def mock_ticket_data():
    """Mock ticket data function - unchanged"""
    with open(r'tests/crmFetchSample.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    ticket_data = {}
    for ticket in data.get("CaseDetails", []):
        case_id = ticket.get("CRM_Case_Number")
        comments = ticket.get("ResolutionRemarks", "")
        ticket["comments"] = comments
        ticket_data[case_id] = ticket

    open_tickets = []
    closed_tickets = []
    for ticket in data.get("CaseDetails", []):
        status = ticket.get("StatusID", "").lower()
        comments = ticket.get("ResolutionRemarks", "")
        ticket_id = ticket.get("CRM_Case_Number")
        crm_service_name = ticket.get("CrmServiceName")
        crm_group_name = ticket.get("CrmGroupName")
        request_details = ticket.get("RequestDetails")
        comments_list = [comments] if comments else []
        ticket_dict = {
            "id": ticket_id,
            "crm_service_name": crm_service_name,
            "crm_group_name": crm_group_name,
            "request_details": request_details,
            "comments": comments_list,
            "resolution": ticket.get("Resolution", "")
        }
        if status == "assigned":
            open_tickets.append(ticket_dict)
        else:
            closed_tickets.append(ticket_dict)

    ticket_data["open"] = open_tickets
    ticket_data["closed"] = closed_tickets
    return ticket_data


# Backward compatibility alias
CRMAgent = CRMAgent

if __name__ == "__main__":
    # Example usage with optimized agent
    print("-------Starting Optimized CRM Agent-------")
    userInfo_file = "tests/userInfo.json"
    
    # Initialize with caching (30 min TTL, max 1000 entries)
    crm_agent = CRMAgent(
        crm_url="http://10.254.115.17:8090", 
        config_path=r'configs/agents_config.yaml',
        llm='llama3.3:latest',
        cache_ttl_minutes=30,
        max_cache_size=1000
    )
    
    print("------Optimized CRM Agent initialized--------")
    with open(userInfo_file, "r") as file:
        userInfo = json.load(file)
        
    user_input = {
        "userId": 0,
        "conversationId": 1234,
        "avatarId": 1,
        "sessionStart": False,
        "conversationTitle": "string",
        "inputType": "TEXT",
        "outputType": "TEXT",
        "channel": "PRIVATE",
        "personId": 0,
        "conversationMessage": "Status of my ticket CAS-02462-T3C9G9",
        "role": "EMPLOYEE",
        "attachments": [],
        "personalInfo": userInfo
    }

    test_state = {
        "userName": "FAHR50684",
        "messages": [HumanMessage(content="Resolution for my ticket - CAS-02462-T3C9G9")]
    }
    
    runtime_config = {
        "configurable": {
            "thread_id": str(user_input["conversationId"]),
            "user_role": user_input["role"], 
            "channel_type": user_input["channel"],
            "session_start": user_input["sessionStart"],
            "userInfo": userInfo
        }
    }
    
    # Test multiple runs to see caching benefits
    for i in range(3):
        print(f"------Test run {i+1}--------")
        start_time = time.time()
        result = asyncio.run(crm_agent.run(test_state, runtime_config=runtime_config))
        elapsed = time.time() - start_time
        print(f"Run {i+1} completed in {elapsed:.2f} seconds")
        print(f"Cache stats: {crm_agent.get_cache_stats()}")
        print("---")
    
    print("-------All tests completed-------")