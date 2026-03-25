# fahr_ai/tests/test_suggestion.py
import unittest
import asyncio
from unittest.mock import patch, MagicMock
from fahr_ai.AIAgents.suggestion_agent import SuggestionAgent, Suggestion
from fahr_ai.AIAgents.base_agent import GraphState
from langchain_core.language_models import BaseLLM
from datetime import datetime, timedelta


class TestSuggestionAgent(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_llm = MagicMock(spec=BaseLLM)
        self.agent = SuggestionAgent(llm=self.mock_llm)
        self.agent.base_url = "https://api.example.com"

    async def test_run_method(self):
        """Test the base agent interface implementation"""
        # Setup mock workflow response
        mock_output = {
            "output": {
                "message": "Hello Test User! Here are some suggestions:",
                "suggestions": ["Test suggestion"],
                "metadata": {
                    "count": 1,
                    "source": "llm",
                    "user_id": 123
                }
            },
            "user_id": 123,
            "user_name": "Test User"
        }
        
        with patch.object(self.agent.workflow, 'ainvoke', return_value=mock_output):
            test_state = GraphState(user_id=123, user_name="Test User")
            result = await self.agent.run(test_state)
            self.assertIn("output", result)
            self.assertIn("suggestions", result["output"])

    @patch('requests.get')
    async def test_get_conversation_texts(self, mock_get):
        """Test conversation text retrieval"""
        # Setup mock responses
        test_time = datetime.now().isoformat()
        mock_get.side_effect = [
            MagicMock(json=lambda: {"data": [{"id": "conv1"}]}),
            MagicMock(json=lambda: {"data": {
                "messages": [{"text": "test message", "createdAt": test_time}]
            }})
        ]

        test_state = GraphState(user_id=123)
        result = self.agent._get_conversation_texts(test_state)
        self.assertEqual(result["texts"], ["test message"])

    async def test_generate_suggestions_with_context(self):
        """Test suggestion generation with conversation context"""
        self.mock_llm.invoke.return_value = "- Check benefits::Benefits\n- View policies::HR"
        
        test_state = GraphState(
            texts=["I have a question about my benefits"],
            user_id=123
        )
        result = self.agent._generate_suggestions(test_state)
        self.assertEqual(len(result["suggestions"]), 2)
        self.assertEqual(result["suggestions"][0].category, "Benefits")

    async def test_generate_suggestions_no_context(self):
        """Test fallback to default suggestions"""
        test_state = GraphState(texts=[], user_id=123)
        result = self.agent._generate_suggestions(test_state)
        self.assertEqual(len(result["suggestions"]), 3)
        self.assertEqual(result["suggestions"][0].confidence, 0.7)

    async def test_format_output(self):
        """Test output formatting"""
        test_suggestions = [
            Suggestion("Test suggestion", "Test", 0.9)
        ]
        test_state = GraphState(
            suggestions=test_suggestions,
            user_id=123,
            user_name="Test User"
        )
        result = self.agent._format_output(test_state)
        self.assertIn("output", result)
        self.assertEqual(result["output"]["suggestions"], ["Test suggestion"])


if __name__ == '__main__':
    unittest.main()