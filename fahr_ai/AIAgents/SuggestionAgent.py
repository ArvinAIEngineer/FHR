import sys
# Add the current directory to sys.path
sys.path.append("./")

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import yaml
import logging
from langchain_core.language_models import BaseChatModel


@dataclass
class SuggestionInfo:
    """Additional information about a suggestion"""
    category: str
    confidence: float = 0.0
    is_context_based: bool = False


class SuggestionService:
    """
    A service that generates suggestions based on conversation context.
    Converted from SuggestionAgent to work as a standalone service.
    """

    def __init__(self,
                 config_path: str = "./configs/agents_config.yaml",
                 llm_model: Optional[BaseChatModel] = None,
                 service_name: str = "SuggestionService"):
        self.logger = logging.getLogger(service_name)
        self.logger.setLevel(logging.INFO)
        
        # Create console handler if no handlers exist
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        self.logger.info("Initializing SuggestionService")
        self.llm = llm_model
        self.suggestion_info: Dict[str, SuggestionInfo] = {}
        self._name = service_name

        # Load prompt from YAML file
        try:
            self.logger.info(f"Loading config from {config_path}")
            with open(config_path, 'r', encoding="utf-8") as file:
                config = yaml.safe_load(file)
                self.prompt_template = config.get('suggestionAgent_prompt', 
                    "Generate 5 relevant suggestions for {primary_topic} based on context: {context}")
        except Exception as e:
            self.logger.warning(f"Could not load config: {e}. Using default prompt.")
            self.prompt_template = "Generate 5 relevant suggestions for {primary_topic} based on context: {context}"

        # Default suggestions for when no context is available
        self.default_suggestions = {
            "HR": [
                "View HR policies",
                "New annual leave calculation method",
                "Flexible working hours options",
                "Submit time off request",
                "Check your benefits",
                "Wellness program benefits",
                "View pay information",
                "Check your leave balance"
            ],
            "Legal": [
                "Recent UAE labor law changes",
                "New FAHR regulations",
                "Digital signature policy",
                "View company policy updates",
                "Review data privacy agreement",
                "Review compliance requirements",
                "Access legal document library",
                "Check UAE labor law changes"
            ],
            "API": [
                "View company holiday calendar",
                "Check your latest payslip",
                "View remaining vacation days",
                "Submit expense report",
                "Request remote work approval"
            ],
            "CRM": [
                "View your CRM tickets",
                "Check ticket status",
                "View recent CRM updates",
                "Submit new CRM ticket",
                "Check CRM case history",
                "View CRM case details",
                "Update CRM ticket",
                "View CRM case comments"
            ],
            "Trends": [
                "Popular topics in HR this month",
                "Trending legal questions",
                "Most requested ERP features",
                "Common questions about leave policy",
                "Frequently asked about work from home"
            ]
        }

        # Keywords that suggest different topic areas
        self.domain_keywords = {
            "HR": ["payslip", "salary", "leave", "vacation", "remote work", "office",
                   "time off", "benefits", "hr", "human resources", "personal", "balance",
                   "fahr", "annual leave", "sick leave", "maternity"],
            "Legal": ["contract", "agreement", "compliance", "policy", "nda",
                      "confidentiality", "legal", "privacy", "regulation", "law",
                      "decree", "legislation", "rights", "entitlement"],
            "API": ["expense", "reimbursement", "report", "inventory", "purchase",
                    "sales", "order", "financial", "payment", "balance", "holiday",
                    "calendar", "approval", "request"],
            "CRM": ["ticket", "crm", "case", "customer", "support", "issue", "problem",
                    "complaint", "feedback", "service", "query", "resolution",
                    "comment", "status", "history", "update", "details"],
            "Trends": ["trend", "trending", "popular", "common", "frequently", "most",
                       "latest", "update", "new", "recent", "changes", "2024", "current"]
        }

    @property
    def name(self) -> str:
        return self._name

    async def generate_suggestions(self, 
                                 messages: List[str], 
                                 ticket_summaries: Optional[str] = None) -> Dict[str, Any]:
        """Generate suggestions based on conversation context"""
        self.logger.info("Generating suggestions")
        
        # Clear previous suggestion info
        self.suggestion_info = {}

        # Check if we have any messages to analyze
        if not messages or len(messages) == 0:
            self.logger.info("No messages found, providing initial suggestions")
            suggestions = self._get_initial_suggestions()
            return {
                "suggestions": suggestions,
                "suggestion_info": self._get_suggestion_info_dict()
            }

        # Get suggestions based on conversation context
        self.logger.info("Generating context-based suggestions")
        suggestions = await self._generate_context_based_suggestions(messages, ticket_summaries)
        
        return {
            "suggestions": suggestions,
            "suggestion_info": self._get_suggestion_info_dict()
        }

    def _get_initial_suggestions(self) -> List[str]:
        """Get initial suggestions when there's no conversation context"""
        self.logger.info("Generating initial suggestions")
        initial_suggestions = []

        # Add the top suggestion from each domain
        for domain, suggestions in self.default_suggestions.items():
            if suggestions:  # Make sure there are suggestions for this domain
                suggestion_text = suggestions[0]
                initial_suggestions.append(suggestion_text)
                self.suggestion_info[suggestion_text] = SuggestionInfo(
                    category=domain,
                    confidence=0.8,
                    is_context_based=False
                )
        
        # Return top suggestions (limit to 5)
        return initial_suggestions[:5]

    async def _generate_context_based_suggestions(self, 
                                                messages: List[str], 
                                                ticket_summaries: Optional[str] = None) -> List[str]:
        """Generate suggestions based on conversation context"""
        self.logger.info("Extracting message texts for context-based suggestions")
        
        # If no message texts, return initial suggestions
        if not messages:
            self.logger.info("No message texts found, providing initial suggestions")
            return self._get_initial_suggestions()

        # Identify potential topic areas based on keywords
        self.logger.info("Identifying potential topics from messages")
        potential_topics = self._identify_topics(messages)

        # If we have a clear topic focus, generate topic-specific suggestions
        if potential_topics:
            self.logger.info("Generating topic-specific suggestions")
            primary_topic = max(potential_topics.items(), key=lambda x: x[1])[0]
            
            # Use the LLM to generate contextual suggestions if available
            if self.llm:
                context = "\n".join(messages[-5:])  # Use last 5 messages for context
                
                formatted_prompt = self.prompt_template.format(
                    primary_topic=primary_topic,
                    crm_ticket_summaries=ticket_summaries or "",
                    context=context
                )
                
                try:
                    result = await self.llm.ainvoke(formatted_prompt)
                    result_content = result.content if hasattr(result, 'content') else str(result)
                    suggestions = [s.strip() for s in result_content.strip().split('\n') if s.strip()]

                    # Store suggestion info
                    for suggestion in suggestions:
                        self.suggestion_info[suggestion] = SuggestionInfo(
                            category=primary_topic,
                            confidence=0.9,
                            is_context_based=True
                        )

                    # If we got suggestions, return them
                    if suggestions:
                        if ['<think>', '</think>'] == suggestions[:2]:
                            return suggestions[2:]
                        return suggestions[:5]
                except Exception as e:
                    self.logger.error(f"Error generating suggestions with LLM: {str(e)}")
                    # Continue to fallback suggestions

        # Fallback: Use default suggestions from the most relevant topic areas
        fallback_suggestions = []

        # Add suggestions from identified topics
        if potential_topics:
            self.logger.info("Sorting potential topics by relevance score")
            sorted_topics = sorted(potential_topics.items(), key=lambda x: x[1], reverse=True)
            for topic, _ in sorted_topics[:2]:  # Top 2 topics
                if topic in self.default_suggestions:
                    fallback_suggestions.extend(self.default_suggestions[topic][:2])

        # If we still need more, add general suggestions
        self.logger.info("Adding general suggestions")
        if len(fallback_suggestions) < 3 and "Trends" in self.default_suggestions:
            fallback_suggestions.extend(
                [s for s in self.default_suggestions["Trends"]
                 if s not in fallback_suggestions][:3]
            )

        # Store suggestion info
        for suggestion in fallback_suggestions:
            # Figure out which category this came from
            category = next((cat for cat, items in self.default_suggestions.items()
                             if suggestion in items), "Trends")

            self.suggestion_info[suggestion] = SuggestionInfo(
                category=category,
                confidence=0.6,
                is_context_based=False
            )
        
        self.logger.info("Returning fallback suggestions")
        return fallback_suggestions[:5]

    def _identify_topics(self, messages: List[str]) -> Dict[str, float]:
        """
        Analyze messages to identify relevant topics.
        Returns a dict of {topic: relevance_score}
        """
        self.logger.info("Identifying topics from messages")
        combined_text = " ".join(messages).lower()
        topic_scores = {}

        for topic, keywords in self.domain_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword.lower() in combined_text:
                    score += 1

            if score > 0:
                # Normalize by number of keywords
                topic_scores[topic] = score / len(keywords)

        # Always include General as a fallback with a minimal score
        if not topic_scores or max(topic_scores.values(), default=0) < 0.3:
            topic_scores["General"] = 0.3

        return topic_scores

    def _get_suggestion_info_dict(self) -> Dict[str, Dict[str, Any]]:
        """Return information about the current suggestions"""
        return {
            suggestion: {
                "category": info.category,
                "confidence": info.confidence,
                "is_context_based": info.is_context_based
            }
            for suggestion, info in self.suggestion_info.items()
        }

    def get_state(self) -> Dict[str, Any]:
        """Return information about the current suggestions"""
        self.logger.info("Getting state of SuggestionService")
        return {
            "suggestion_info": self._get_suggestion_info_dict()
        }



if __name__ == "__main__":
    import asyncio
    from langchain_ollama import ChatOllama
    from langchain_core.messages import HumanMessage, AIMessage
    # Initialize models and vectorstore
    llm = ChatOllama(model="llama3.2:3b", temperature=0)

    # Initialize HRAgent
    agent = SuggestionAgent(llm_model=llm)

    # Create a GraphState with the query as a message
    messages = [HumanMessage(
        content='Explain what a leave balance is based on law in 2019 and what is the difference regarding the previous years',
        additional_kwargs={}, response_metadata={}, id='912dfecf-efc7-4129-bd7a-dcf5e37006aa'),
    AIMessage(
        content='I can provide information regarding leave balances, but to detail the legal changes in 2019, I need to route you to our HR agent. They have access to the specific legal documentation and policy updates concerning leave entitlements from that year. They’ll be able to explain the differences compared to previous years’ legislation.',
        additional_kwargs={}, response_metadata={}, id='7c616e92-3b51-4190-8bd1-81ad76c3e722'),
    AIMessage(
        content='Okay, let’s clarify your understanding of leave balances according to FAHR regulations as of 2019, considering the changes from previous years.\n\nAs of 2019, due to Federal Decree-Law No. 33 of 2017, the minimum annual leave entitlement for employees working a standard 48-hour week increased to **30 days**.  This was a key change! Previously, the minimum was just 15 days for similar roles.\n\nHere’s how it works:\n\n*   **Accrual:** You accrue leave based on your length of service. The exact rate is determined by your employment contract or your company’s policy, but the law sets a *minimum* accrual rate.\n*   **Carryover:** You can carry over a *maximum* of **15 days** of accrued leave to the following year. Any days beyond this are usually lost.\n*   **Important Note:** Your company’s policy *could* offer more generous leave, but it *must* always meet the minimum legal requirement of 30 days for annual leave.\n\n**Difference from Previous Years (Pre-2017):**\n\nBefore 2017, leave entitlements were *highly* variable.  Companies could offer anything from 10 to 20 days, dependent on the industry and their own policies. The biggest change with the 2017 law was creating a standardized minimum.\n\n**To help me give you more precise information, could you tell me:**\n\n*   What type of leave are you most interested in (annual, sick, maternity, etc.)?\n*   Are you employed in a specific sector, such as government, private sector, or perhaps in a particular industry (like oil and gas or healthcare)?',
        additional_kwargs={}, response_metadata={}, id='18e3906f-f754-45aa-ac04-2184fc602db4'),
    AIMessage(
        content="I’m connecting you to our HR agent who can explain the specific details of your leave balance based on the regulations of 2019. They'll be able to answer your questions accurately.",
        additional_kwargs={}, response_metadata={}, id='a61c8abc-ae36-42b2-9299-12c5b03597e5'),
    AIMessage(
        content="Okay, here’s an explanation of leave balances based on law in 2019, based on the documents you’ve provided, in English:\n\n**Leave Balance Explained (2019 - UAE Law & FAHR Regulations)**\n\nAs of 2019, the rules around leave in the UAE were significantly changed by the UAE Labor Law (Federal Decree-Law No. 33 of 2017) and implemented by FAHR. Here’s a breakdown:\n\n**1. Minimum Annual Leave:**\n\n*   **The Minimum Standard:** The law set a *minimum* of 30 calendar days of paid annual leave for employees working a standard 48-hour week. This was a major shift from previous practices.\n*   **Accrual Based on Service:** The number of days you earned each year depended on how long you’d worked for the same employer:\n    *   **Up to 5 Years:**  You’d earn 0.5 days of leave per month you worked. (Example: 5 years * 12 months/year = 60 months * 0.5 days/month = 30 days)\n    *   **Over 5 Years:** You’d earn 1 day of leave per month of service. (Example: 6 years of service * 1 day/month = 72 days)\n\n**2. Carryover Limit:**\n\n*   **Maximum Carryover:** You could *carry over* a maximum of 15 days of unused leave to the *next* calendar year. This meant if you didn’t use all 30 days, you could roll 15 of them over.\n*   **Lost Unused Leave:**  Crucially, *any* leave exceeding 15 days at the end of the year would be *lost*. It couldn't be saved for later.\n\n**Key Differences From Before 2017:**\n\nBefore 2017, there were no federal laws setting a minimum for leave. Companies could offer anything from 15 to 20 days, based on their own company policies.  The 2017 law made 30 days the absolute minimum.\n\n**Important Note:** This information is based solely on the documents provided, and does not constitute legal advice.\n\n\n\n\n\nDo you want me to explain any specific part of this in more detail, or perhaps look at how this applies to a particular length of service (e.g., someone with 7 years of service)?",
        additional_kwargs={}, response_metadata={}, id='c608fb12-ebf0-476b-a71b-9f4a208254d4'),
    AIMessage(
    content='Here’s a detailed explanation of leave balances according to law in 2019, based on the regulations of FAHR. To help me give you more precise information, could you tell me: What type of leave are you most interested in (annual, sick, maternity, etc.)? ',
    additional_kwargs={}, response_metadata={})]

    state = GraphState(
        messages=messages,
        memory={},
        suggestions=[]
    )

    print("Processing...\n")

    # Run the agent with the query
    response = agent.run(state)

    # Print the response
    print("=" * 80)
    print("Suggestion AGENT RESPONSE:")
    print(response["suggestions"])
    print("=" * 80)
    print("\n")