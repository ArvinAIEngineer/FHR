# Standard Library Imports
import sys
from datetime import datetime, timedelta, timezone
from dateutil.parser import parse
from typing import Any, List, Optional, Dict, Literal

# Third-Party Library Imports
import yaml
from IPython.display import Image
from sentence_transformers import CrossEncoder

# LangChain Core Imports
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import BaseTool, tool
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.runnables.graph import MermaidDrawMethod

# LangChain Community & Extended Imports
from langchain_community.retrievers import BM25Retriever

# LangChain Main Libraries
from langchain.chains import RetrievalQA
from langchain.vectorstores import VectorStore
from langchain.chat_models.base import BaseChatModel
from langchain.retrievers import EnsembleRetriever
from langchain.schema import Document

# LangGraph Imports
from langgraph.graph import START, END, StateGraph
from langgraph.graph.message import MessagesState
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode

# Project-Specific Imports
# Add the current directory to the Python path
sys.path.append("./")
from workflows.base_workflow import BaseWorkflow
from utils.logger import get_logger
import logging


# Define custom state that includes memory
class EnhancedState(MessagesState):
    memory: Dict[str, Any] = {},
    conversation_id: int

class RAGWorkflow(BaseWorkflow):
    """
    Retrieval-Augmented Generation workflow for information retrieval and answering.
    Inherits from BaseWorkflow.
    """

    def __init__(
        self,
        vectorstore: Optional[VectorStore] = None,
        llm_model: Optional[BaseChatModel] = None,
        workflow_name: str = "RAGWorkflow",
        config_path: str = "./configs/rag_workflow_config.yaml"
    ):
        """
        Initialize the RAGWorkflow with a vectorstore, language model, and configuration.

        Args:
            vectorstore: Instance of VectorStore used for document retrieval.
            llm_model: Language model instance used to generate responses.
            workflow_name: Optional name for the workflow instance.
            config_path: Path to the YAML config file containing prompts and retrieval settings.
        """
        self.base_logger = get_logger()
        self.base_logger.setLevel(logging.INFO)

        self._name = workflow_name
        self._internal_memory = {}

        self.vectorstore = vectorstore
        self.model = llm_model

       
        # Load configuration
        with open(config_path, "r") as file:
            self.config = yaml.safe_load(file)
            self.prompts = self.config.get("prompts", {})
            self.retrieval_config = self.config.get("retrival_config", {})

        # Add configuration for forced retrieval
        self.force_retrieval = self.retrieval_config.get("force_document_retrieval", True)
        self.min_required_docs = self.retrieval_config.get("min_required_documents", 1)
        
         # Initialize reranker model
        if self.retrieval_config.get("use_reranker", False):
            rereanker_model_name = self.retrieval_config.get("rereanker", "BAAI/bge-reranker-v2-m3")
            self.reranker = CrossEncoder(rereanker_model_name)
            self.base_logger.info(f"Initialized Reranker {rereanker_model_name} successfully")

        # Initialize BM25 retriever if enabled
        self.bm25_retriever = None
        if self.retrieval_config.get("enable_bm25_ensemble", False):
            collection = self.vectorstore._collection
            all_docs = collection.get(
                include=["documents", "metadatas"],
                limit=self.retrieval_config.get("bm25_rertival_doc_limit", 1000)
            )

            docs = [
                Document(page_content=doc, metadata=meta)
                for doc, meta in zip(all_docs["documents"], all_docs["metadatas"])
            ]

            if docs:
                self.bm25_retriever = BM25Retriever.from_documents(docs)
                self.base_logger.info(f"[BM25 Init] Loaded {len(docs)} documents for BM25Retriever.")
            else:
                self.base_logger.warning(f"[BM25 Init] No documents found in collection '{collection.name}'.")

        # Initialize tools and workflow
        self.tools = self._create_tools()
        self.workflow = StateGraph(EnhancedState)
        self.app = self.build_workflow()

    def format_docs(self,docs):
        formatted = []
        for doc in docs:
            metadata = doc.metadata
            formatted.append({
                "chunkText": doc.page_content,
                "documentId": metadata.get("document_id"),
                "documentName": metadata.get("document_name"),
                "pageNumber": metadata.get("page_number"),
                "page_image": metadata.get("page_image"),
            })
        return formatted

    def retrieve_content_from_vector(self, query, fallback_attempts=3):
        """Enhanced retrieval with multiple fallback strategies."""
        
        # Try different retrieval strategies
        strategies = [
            {"k": self.retrieval_config.get("top_k", 3)},  # Normal retrieval
            {"k": self.retrieval_config.get("top_k", 3) * 2},  # Double the results
            {"k": 10},  # Even more results
        ]
        
        for attempt, strategy in enumerate(strategies):
            self.base_logger.info(f"Retrieval attempt {attempt + 1} with strategy: {strategy}")
            
            dense = self.vectorstore.as_retriever(search_kwargs=strategy)
            
            if self.bm25_retriever is None:
                self.base_logger.info("Using Dense retrieval")
                results = dense.invoke(query)
            else:
                hybrid = EnsembleRetriever(
                    retrievers=[dense, self.bm25_retriever], 
                    weights=[1-self.retrieval_config.get("bm25_rertival_weight", 0.5), 
                            self.retrieval_config.get("bm25_rertival_weight", 0.5)]
                )
                results = hybrid.invoke(query)
                self.base_logger.info("Using Ensemble retrieval")

            # If we got results, process them
            if results:
                # Your existing filtering logic...
                valid_docs = []
                for doc in results:
                    date_str = doc.metadata.get("processed_at")
                    if date_str:
                        try:
                            processed_date = parse(date_str)
                            if processed_date.tzinfo is None:
                                processed_date = processed_date.replace(tzinfo=timezone.utc)
                            valid_docs.append(doc)
                        except Exception as e:
                            self.base_logger.warning(f"Invalid processed_at format: {date_str} — skipping doc")

                if valid_docs:
                    # Apply reranking if enabled
                    if self.retrieval_config.get("use_reranker", False):
                        doc_pairs = [(query, doc.page_content) for doc in valid_docs]
                        scores = self.reranker.predict(doc_pairs)
                        reranked = sorted(zip(valid_docs, scores), key=lambda x: x[1], reverse=True)
                        top_n = self.retrieval_config.get("top_k", 3)
                        top_docs = [doc for doc, _ in reranked[:top_n]]
                        return self.format_docs(top_docs)
                    
                    return self.format_docs(valid_docs)
        
        # If all strategies failed, log error and return empty (or raise exception)
        self.base_logger.error(f"All retrieval strategies failed for query: {query}")
        return []


    def _create_tools(self) -> List[BaseTool]:
        """Create and return all the tools."""

        @tool
        def retrieve_context(query: str) -> dict:
            """Fetch relevant context from the vector store based on the user's query."""
            self.base_logger.info(f"Retrieving context for query: {query}")
            results = self.retrieve_content_from_vector(query)

            if not results:
                self.base_logger.info("No relevant documents found.")
                return {
                    "context": "[NO_DOCUMENTS_FOUND]",
                    "context_chunks": [],
                    "referenceData": []
                }

            context_text = "\n".join(doc["chunkText"] for doc in results)
            return {
                "context": context_text,
                "context_chunks": results,
                "referenceData": results
            }

        @tool
        def refine_query(original_query: str, history: Optional[str] = "") -> str:
            """Refine a query using both the original query and previous chat history."""
            self.base_logger.info(f"Refining query with history")
            prompt = ChatPromptTemplate.from_template(self.prompts['refine_query_with_history_prompt'])  # New prompt template
            chain = prompt | self.model | StrOutputParser()
            refined_query = chain.invoke({
                "original_query": original_query,
                "history": history
            })
            self.base_logger.info(f"Refined query: {refined_query}")
            return refined_query

        @tool
        def multi_hop_retrieval(query: str) -> dict:
            """Performs multi-hop retrieval to answer complex queries by combining information from multiple sources."""

            self.base_logger.info("Starting multi-hop retrieval for query")

            # First hop: Retrieve initial context
            first_hop_results = self.retrieve_content_from_vector(query)
            first_hop_context = "\n".join(doc["chunkText"] for doc in first_hop_results)
            self.base_logger.info(f"First hop context retrieved: {first_hop_context}")

            # Generate follow-up query based on the first context
            followup_prompt = ChatPromptTemplate.from_template(self.prompts['followup_prompt'])
            followup_chain = followup_prompt | self.model | StrOutputParser()
            followup_query = followup_chain.invoke({"query": query, "context": first_hop_context})
            self.base_logger.info(f"Generated follow-up query: {followup_query}")

            # Second hop: Retrieve additional context based on follow-up query
            second_hop_results = self.retrieve_content_from_vector(followup_query)
            second_hop_context = "\n".join(doc["chunkText"] for doc in second_hop_results)
            self.base_logger.info(f"Second hop context retrieved: {second_hop_context}")

            # Combine contexts from both hops
            combined_context = (
                f"Initial search results:\n{first_hop_context}\n\n"
                f"Follow-up search results:\n{second_hop_context}"
            )
            self.base_logger.info("Combined multi-hop context prepared.")

            # Return combined context and all retrieved reference data
            return {
                "context": combined_context,
                "referenceData": first_hop_results + second_hop_results
            }

        @tool
        def validate_response(query: str, proposed_answer: str,context: str) -> str:
            """Validate the proposed answer against the retrieved context to ensure accuracy."""
            # Retrieve relevant context for validation
            self.base_logger.info("Validating response...")

            validation_prompt = ChatPromptTemplate.from_template(self.prompts['validation_prompt'])
            validation_chain = validation_prompt | self.model | StrOutputParser()
            validation_result = validation_chain.invoke({
                "query": query,
                "answer": proposed_answer,
                "context": context
            })
            self.base_logger.info(f"Validation result: {validation_result}")
            return validation_result

        @tool
        def incorporate_feedback(query: str, previous_answer: str, feedback: str) -> str:
            """Incorporate user feedback to improve the answer."""
            # Get fresh context
            self.base_logger.info("Incorporating feedback...")
            retriever = self.vectorstore.as_retriever(search_kwargs={"k": 3})
            context = retriever.invoke(query)
            context_text = "\n".join([doc.page_content for doc in context])

            feedback_prompt = ChatPromptTemplate.from_template(self.prompts['feedback_prompt'])
            feedback_chain = feedback_prompt | self.model | StrOutputParser()
            improved_answer = feedback_chain.invoke({
                "query": query,
                "previous_answer": previous_answer,
                "feedback": feedback,
                "context": context_text
            })
            self.base_logger.info(f"Improved answer: {improved_answer}")
            return improved_answer

        @tool
        def self_correct_with_context(query: str, previous_answer: str, context: str, feedback: str) -> str:
            """Refine the answer using validation feedback and context."""
            self.base_logger.info("Refining answer based on validation feedback")
            prompt = ChatPromptTemplate.from_template(self.prompts['self_correction_prompt'])
            chain = prompt | self.model | StrOutputParser()
            improved_answer = chain.invoke({
                "query": query,
                "previous_answer": previous_answer,
                "context": context,
                "feedback": feedback
            })
            self.base_logger.info(f"Refined answer: {improved_answer}")
            return improved_answer


        return [
            retrieve_context,
            refine_query,
            multi_hop_retrieval,
            validate_response,
            incorporate_feedback,
            # retrieve_conversation_context,
            self_correct_with_context
        ]

    # 2. Add a helper method to extract key terms for fallback searches
    def _extract_key_terms(self, query: str) -> str:
        """Extract key terms from query for broader search."""
        import re
        # Remove common stop words and extract meaningful terms
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'how', 'what', 'when', 'where', 'why', 'is', 'are', 'was', 'were'}
        words = re.findall(r'\w+', query.lower())
        key_terms = [word for word in words if word not in stop_words and len(word) > 2]
        return ' '.join(key_terms[:3])  # Take top 3 key terms
    
    def build_workflow(self) -> Any:
        """
        Build and compile the RAG workflow using LangGraph.
        """
        # Create tool node for the LangGraph
        self.base_logger.info("Building workflow")
        tool_node = ToolNode(self.tools)

        # Function to decide the next action in the workflow
        self
        def route_action(state: EnhancedState) -> Literal["multi_hop", "validation", "correction_required", END]:
            conversation_id = state["conversation_id"]
            logger = get_logger(conversation_id)
            logger.setLevel(logging.INFO)
            logger.info("Routing action based on current state")
            messages = state['messages']
            last_message = messages[-1]
            memory = state.get("memory", {})
            stage = memory.get("stage", "")
            validation_status = memory.get("validation_status", "")

            if stage == "corrected":
                memory["stage"] = "revalidated"
                return "validation"
            
            # If this is a response after initial retrieval, go to validation
            logger.info(f"Current stage: {stage} and validation_status: {validation_status}")
            if stage == "initial_retrieval":
                memory["stage"] = "validation"
                return "validation"

            # Handle forced multi-hop when no documents found - route to existing multi_hop node
            if stage == "force_multi_hop" or memory.get("force_multi_hop", False):
                memory["stage"] = "multi_hop"
                memory["force_multi_hop"] = False
                return "multi_hop"  # Route to existing multi_hop node

            # If this is after validation and we need more info, go to multi hop or self correction
            if stage == "validation":
                if validation_status == "needs_more_info":
                    memory["stage"] = "multi_hop"
                    return "multi_hop"
                elif validation_status == "incorrect":
                    memory["stage"] = "correction_required"
                    return "correction_required"
                return END
             
            if stage == "revalidated":
                if validation_status in {"needs_more_info", "incorrect"}:
                    logger.info("Correction failed. Escalating to multi-hop.")
                    memory["stage"] = "multi_hop"
                    return "multi_hop"
                return END
            
            if stage == "multi_hop_complete":
                memory["stage"] = "post_multihop_validation"
                return "validation"
            
            if stage == "post_multihop_validation":
                if validation_status != "correct":
                    logger.warning("Post multi-hop result still invalid. Responding with fallback.")
                    memory["stage"] = "fallback"
                    memory["fallback_reason"] = f"Validation failed after multi-hop. Status: {validation_status}"
                    return END
                return END

            # Otherwise, end the workflow
            return END
        
        def get_conversation_history(messages: List, n_turns: int = 3) -> str:
            context_lines = []
            for msg in messages[-(n_turns * 2):-1]:  # Exclude last (current query)
                if isinstance(msg, HumanMessage):
                    context_lines.append(f"User: {msg.content}")
                elif isinstance(msg, AIMessage):
                    context_lines.append(f"Agent: {msg.content}")
            return "\n".join(context_lines)

        # Function to refine the query before retrieval
        def refine_input_query(state: EnhancedState):
            conversation_id = state["conversation_id"]
            logger = get_logger(conversation_id)
            logger.setLevel(logging.INFO)
            logger.info("Refining input query")
            messages = state['messages']
            last_message = messages[-1]
            logger.info(f"message state from refine_input_query: {state['messages']}")
            if isinstance(last_message, HumanMessage):
                original_query = last_message.content
                
                history_context = get_conversation_history(state["messages"])
                
                logger.info(f"Refining query with history")

                # Find the refine_query tool
                refine_query = next((t for t in self.tools if t.name == "refine_query"), None)
                logger.info(f"[Graph Node] refine_query tool {refine_query}")
                if refine_query:
                    # Call the refine_query tool
                    refined_query = refine_query.invoke({
                     "original_query": original_query,
                    "history": history_context
                        })

                    # Store the original and refined queries in memory
                    if "memory" not in state:
                        state["memory"] = {}
                    state["memory"]["original_query"] = original_query
                    state["memory"]["refined_query"] = refined_query
                    state["memory"]["stage"] = "query_refined"

                    # Add a message indicating the query was refined
                    tool_message = ToolMessage(
                        content=f"Query refined: '{refined_query}'",
                        tool_call_id="query_refinement"
                    )

                    # Update the state
                    return {"messages": messages + [tool_message]}
            logger.info(f"No refinement needed, hence returning original messages")
            return {"messages": messages}

        # Function for initial retrieval after query refinement
        def perform_initial_retrieval(state: EnhancedState):
            conversation_id = state["conversation_id"]
            logger = get_logger(conversation_id)
            logger.setLevel(logging.INFO)
            logger.info("Performing initial retrieval")
            memory = state.get("memory", {})
            refined_query = memory.get("refined_query")

            if refined_query:
                # Find the retrieve_context tool
                retrieve_context = next((t for t in self.tools if t.name == "retrieve_context"), None)

                if retrieve_context:
                    # Retrieve context using the refined query
                    result = retrieve_context.invoke(refined_query)

                    # FORCE RETRIEVAL: If no documents found, try with original query or broader search
                    if isinstance(result, dict) and result.get("context", "").strip() == "[NO_DOCUMENTS_FOUND]":
                        logger.warning("No documents found with refined query. Trying with original query.")
                        
                        # Try with original query
                        original_query = memory.get("original_query", refined_query)
                        result = retrieve_context.invoke(original_query)
                        
                        # If still no results, try with broader/simplified query
                        if result.get("context", "").strip() == "[NO_DOCUMENTS_FOUND]":
                            # Extract key terms and try again
                            key_terms = self._extract_key_terms(original_query)
                            if key_terms:
                                logger.warning(f"Trying with key terms: {key_terms}")
                                result = retrieve_context.invoke(key_terms)
                        
                        # If STILL no results, set flag for multi-hop instead of creating new node
                        if result.get("context", "").strip() == "[NO_DOCUMENTS_FOUND]":
                            logger.error("Initial retrieval failed completely. Setting up for multi-hop.")
                            
                            # Set flag to force multi-hop retrieval
                            state["memory"]["force_multi_hop"] = True
                            state["memory"]["stage"] = "force_multi_hop"
                            
                            # Create a minimal context to avoid breaking the flow
                            state["memory"]["context"] = "[INITIAL_RETRIEVAL_FAILED]"
                            state["memory"]["reference_data"] = []
                            
                            tool_message = ToolMessage(
                                content="Initial retrieval failed. Will attempt multi-hop search.",
                                tool_call_id="initial_retrieval"
                            )
                            return {"messages": state["messages"] + [tool_message]}
                    
                    # Store context and reference data
                    state["memory"]["context"] = result["context"]
                    state["memory"]["reference_data"] = result.get("referenceData", [])
                    state["memory"]["stage"] = "initial_retrieval"

                    tool_message = ToolMessage(
                        content=f"Retrieved relevant context:\n\n{result['context']}",
                        tool_call_id="initial_retrieval"
                    )
                    return {"messages": state["messages"] + [tool_message]}

            logger.error("No query available for initial retrieval")
            return {"messages": state["messages"]}

        # Function for multi-hop retrieval
        def perform_multi_hop(state: EnhancedState):
            conversation_id = state["conversation_id"]
            logger = get_logger(conversation_id)
            logger.setLevel(logging.INFO)
            logger.info("Performing multi-hop retrieval")
            memory = state.get("memory", {})
            original_query = memory.get("original_query")
            
            # Check if this is a forced multi-hop due to initial retrieval failure
            is_forced = memory.get("force_multi_hop", False)
            
            if original_query:
                # Find the multi_hop_retrieval tool
                multi_hop_retrieval_tool = next((t for t in self.tools if t.name == "multi_hop_retrieval"), None)
                if multi_hop_retrieval_tool:
                    # Perform multi-hop retrieval
                    multi_hop_result = multi_hop_retrieval_tool.invoke(original_query)
                    
                    # If this was forced and we still get no results, try alternative strategies
                    if is_forced and not multi_hop_result.get("context"):
                        logger.warning("Forced multi-hop also failed. Trying alternative search strategies.")
                        
                        # Try with simplified query
                        simplified_query = self._extract_key_terms(original_query)
                        if simplified_query:
                            multi_hop_result = multi_hop_retrieval_tool.invoke(simplified_query)
                    
                    # Create a message with the multi-hop results
                    tool_message = ToolMessage(
                        content=f"Additional context from multi-hop retrieval:\n\n{multi_hop_result['context']}",
                        tool_call_id="multi_hop_retrieval"
                    )
                    
                    # Update memory
                    if "memory" not in state:
                        state["memory"] = {}
                    state["memory"]["multi_hop_context"] = multi_hop_result["context"]
                    state["memory"]["multi_hop_reference_data"] = multi_hop_result.get("referenceData", [])
                    state["memory"]["stage"] = "multi_hop_complete"
                    state["memory"]["force_multi_hop"] = False  # Clear the flag
                    
                    # Add the tool message to the conversation
                    logger.info(f"Multi-hop retrieval result: {multi_hop_result}")
                    return {"messages": state["messages"] + [tool_message]}
                    
            logger.info(f"No multi-hop retrieval needed, returning original messages")
            return {"messages": state["messages"]}

        # Function to validate the latest AI response
        def validate_current_response(state: EnhancedState):
            conversation_id = state["conversation_id"]
            logger = get_logger(conversation_id)
            logger.setLevel(logging.INFO)
            logger.info("Starting response validation process.")

            messages = state.get("messages", [])
            memory = state.get("memory", {})

            # Retrieve the most recent AI message
            proposed_answer = next((msg.content for msg in reversed(messages) if isinstance(msg, AIMessage)), None)
            original_query = memory.get("original_query")

            if not (proposed_answer and original_query):
                logger.warning("Missing proposed answer or original query. Skipping validation.")
                return {"messages": messages}

            validate_tool = self.get_tool_by_name("validate_response")
            if not validate_tool:
                logger.warning("Validation tool not found.")
                return {"messages": messages}

            # Select appropriate context for validation
            if memory.get("stage") == "post_multihop_validation":
                validation_context = memory.get("multi_hop_context", "")
                logger.info("Using multi-hop context for validation.")
            else:
                validation_context = memory.get("context", "")
                logger.info("Using initial context for validation.")

            # Perform validation
            validation_output = validate_tool.func(
                query=original_query,
                proposed_answer=proposed_answer,
                context=validation_context
            )

            # Parse validation result
            validation_status = "unknown"
            validation_feedback = validation_output

            if validation_output.startswith("- Validation:"):
                for line in validation_output.splitlines():
                    if "Validation:" in line:
                        validation_status = (
                            line.split(":", 1)[1].strip().lower().replace(" ", "_").replace("*", "")
                        )
                    elif "Feedback:" in line:
                        validation_feedback = line.split(":", 1)[1].strip()

            memory["validation_status"] = validation_status
            memory["validation_result"] = validation_feedback

            tool_message = ToolMessage(
                content=f"Validation status: {validation_status}\nFeedback: {validation_feedback}",
                tool_call_id="validation"
            )

            return {"messages": messages + [tool_message]}

        def perform_self_correction(state: EnhancedState):
            memory = state.get("memory", {})
            query = memory.get("original_query")
            context = memory.get("context")
            feedback = memory.get("validation_result")
            conversation_id = state["conversation_id"]
            logger = get_logger(conversation_id)
            logger.setLevel(logging.INFO)
            logger.info("Performing self-correction based on validation feedback")


            previous_answer = next((msg.content for msg in reversed(state["messages"]) if isinstance(msg, AIMessage)), None)

            tool = self.get_tool_by_name("self_correct_with_context")
            if tool and query and previous_answer and context and feedback:
                improved = tool.func(query=query, previous_answer=previous_answer, context=context, feedback=feedback)
                AI_message = AIMessage(
                    content=f"Refined Answer:\n{improved}",
                    tool_call_id="self_correct_with_context"
                )
                memory["stage"] = "corrected"
                return {"messages": state["messages"] + [AI_message]}

            logger.warning("Insufficient data for self-correction.")
            return {"messages": state["messages"]}

        # Function that invokes the model to generate a response
        def call_model(state: EnhancedState):
            messages = state['messages']
            memory = state.get("memory", {})
            stage = memory.get("stage", "")
            conversation_id = state["conversation_id"]
            logger = get_logger(conversation_id)
            logger.setLevel(logging.INFO)
            # Handle different failure scenarios
            if stage == "fallback":
                fallback_message = "I'm unable to confidently answer this based on the available information."
                logger.info(f"Returning fallback response due to: {memory.get('fallback_reason', '')}")
                return {"messages": state["messages"] + [AIMessage(content=fallback_message)]}
            
            elif stage == "skipped_due_to_no_documents":
                logger.info("Skipping LLM invocation due to no documents.")
                return {"messages": state["messages"]}
            
            # Handle forced multi-hop scenario - skip model call and let routing handle it
            elif stage == "force_multi_hop":
                logger.info("Forcing multi-hop retrieval due to initial retrieval failure.")
                # Don't call the model, let the routing system handle multi-hop
                return {"messages": state["messages"]}
            
            elif stage == "initial_retrieval":
                # Check if we actually have valid context
                context = memory.get("context", "")
                if context == "[INITIAL_RETRIEVAL_FAILED]":
                    # Skip model call, let routing handle multi-hop
                    logger.info("Initial retrieval failed, skipping model call for multi-hop.")
                    return {"messages": state["messages"]}
                
                instruction = self.prompts['initial_retrieval_instruction']
                query = memory.get("refined_query")
                final_prompt = instruction.format(query=query, context=context)
                logger.info(f"Calling call model with initial_retrieval_instruction")

            elif stage == "validated":
                instruction = self.prompts['validated_instruction']
                query = memory.get("original_query")
                context = memory.get("context", "")
                previous_answer = next((m.content for m in reversed(messages) if isinstance(m, AIMessage)), "")
                final_prompt = instruction.format(query=query, context=context, previous_answer=previous_answer)
                logger.info(f"Calling call model with validated_instruction")
            
            elif stage == "multi_hop_complete":
                instruction = self.prompts['multi_hop_complete_instruction']
                query = memory.get("original_query")
                context = memory.get("multi_hop_context", "")
                final_prompt = instruction.format(query=query, context=context)
                logger.info(f"Calling call model with multi_hop_complete_instruction")

            else:
                logger.info(f"No instruction matched for stage '{stage}', skipping model call.")
                return {"messages": state["messages"]}

            # Add the instruction as a system message and call the model
            system_message = SystemMessage(content=instruction)
            logger.info(f"messages from call model: {messages + [system_message]}")
            
            response = self.model.invoke([
                HumanMessage(content=final_prompt)
            ])
            logger.info(f"Model response: {response}")

            return {"messages": state["messages"] + [response]}

        # Add nodes to the graph
        self.base_logger.info("Adding nodes to the workflow")
        self.workflow.add_node("agent", call_model)
        self.workflow.add_node("query_refinement", refine_input_query)
        self.workflow.add_node("multi_hop", perform_multi_hop)
        self.workflow.add_node("validation", validate_current_response)
        self.workflow.add_node("initial_retrieval", perform_initial_retrieval)
        self.workflow.add_node("correction_required", perform_self_correction)


        # Connect nodes with a clear, linear flow (no cycles)
        self.base_logger.info("Connecting nodes in the workflow")
        self.workflow.add_edge(START, "query_refinement")  # Start with query refinement
        self.workflow.add_edge("query_refinement", "initial_retrieval")  # Then do initial retrieval
        self.workflow.add_edge("initial_retrieval", "agent")  # Generate first response

        # Conditional edges only from agent to specific next steps (no self-loop)
        self.base_logger.info("Adding conditional edges")
        self.workflow.add_conditional_edges("agent", route_action)  # Decision after the "agent" node

        # Return paths to agent from tools, multi_hop, and validation
        self.base_logger.info("Adding return paths to agent")
        self.workflow.add_edge("multi_hop", "agent")  # After multi-hop, go back to agent
        self.workflow.add_edge("validation", "agent")  # After validation, go back to agent
        self.workflow.add_edge("correction_required", "agent")  # After correction_required, go back to agent


        # Configure memory to persist the state
        checkpointer = MemorySaver()

        # Compile the graph into a LangChain Runnable application
        app = self.workflow.compile(checkpointer=checkpointer)

        # Visualize and save the workflow graph
        # Image(app.get_graph().draw_mermaid_png(output_file_path="rag_workflow.png", draw_method=MermaidDrawMethod.PYPPETEER))

        return app

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the RAG workflow with the given state.

        Args:
            state: Dictionary containing input, history, and other state information

        Returns:
            Updated state with workflow results
        """
        # Convert state to the format expected by LangGraph
        self.base_logger.info("Running the workflow with the provided state")
        # self.base_logger.debug(f"Initial state: {state}")
        messages_state = {"messages": []}

        # If there's input in the state, add it as a human message
        if "input" in state and state["input"]:
            self.base_logger.info(f"User input: {state['input']}")
            messages_state["messages"].append(HumanMessage(content=state["input"]))

        # If there's history, add it to the messages
        if "history" in state and state["history"]:
            self.base_logger.info(f"Conversation history: {state['history']}")
            for turn in state["history"]:
                if "input" in turn:
                    messages_state["messages"].append(HumanMessage(content=turn["input"]))
                if "output" in turn:
                    messages_state["messages"].append(AIMessage(content=turn["output"]))

        # If there's memory in the state, add it to the EnhancedState
        if "memory" in state:
            self.base_logger.info(f"Memory: {state['memory']}")
            messages_state["memory"] = state["memory"]

        # Run the workflow
        config = RunnableConfig(configurable={"thread_id": str(id(state))})
        result = self.app.invoke(messages_state, config)

        # Extract the AI's response from the result
        ai_messages = [msg for msg in result["messages"] if isinstance(msg, AIMessage)]
        if ai_messages:
            state["output"] = ai_messages[-1].content

        # Update the state's memory from the workflow's memory
        if "memory" in result:
            self.base_logger.info(f"Updating state memory: {result['memory']}")
            state["memory"] = result["memory"]

        # Store workflow execution info in internal memory
        self._internal_memory["last_execution"] = {
            "input": state.get("input", ""),
            "output": state.get("output", ""),
            "timestamp": None  # Could add timestamp here if needed
        }
        self.base_logger.info(f"Workflow execution result: {state}")

        return state

    def reset(self) -> None:
        """
        Resets the workflow's internal state or memory.
        """
        self.base_logger.info("Resetting workflow internal memory")
        self._internal_memory = {}

    def get_state(self) -> Dict[str, Any]:
        """
        Returns the workflow's internal state.
        """
        self.base_logger.info("Getting workflow internal memory")
        return self._internal_memory

    def get_tool_by_name(self, tool_name: str) -> Optional[BaseTool]:
        """Get a tool by its name."""
        for tool in self.tools:
            if tool.name == tool_name:
                return tool
        return None
