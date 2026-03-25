import unittest
import asyncio
from unittest.mock import patch, MagicMock
from fahr_ai.AIAgents.response_review_agent import ResponseAgent, ResponseReview
from fahr_ai.AIAgents.base_agent import GraphState
from langchain_core.language_models import BaseLLM


class TestResponseAgent(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_llm = MagicMock(spec=BaseLLM)
        self.agent = ResponseAgent(llm=self.mock_llm)

        # Mock the workflow execution
        self.workflow_patch = patch.object(
            self.agent.workflow,
            'ainvoke',
            return_value=ResponseReview(
                response="Mock response",
                is_approved=True
            )
        )
        self.mock_workflow = self.workflow_patch.start()

    def tearDown(self):
        self.workflow_patch.stop()

    async def test_run_method(self):
        input_state = GraphState(input="test query", memory={})
        result = await self.agent.run(input_state)
        
        self.assertIsInstance(result, ResponseReview)
        self.assertTrue(result.is_approved)

    async def test_approved_response_workflow(self):
        self.mock_workflow.return_value = ResponseReview(
            response="Approved response",
            is_approved=True
        )

        input_state = GraphState(input="query about benefits", memory={})
        result = await self.agent.run(input_state)

        self.assertTrue(result.is_approved)
        self.assertEqual(result.response, "Approved response")

    async def test_rejected_response_workflow(self):
        self.mock_workflow.return_value = ResponseReview(
            response="Rejected response",
            is_approved=False,
            issues=["Issue 1", "Issue 2"]
        )

        input_state = GraphState(input="problematic query", memory={})
        result = await self.agent.run(input_state)

        self.assertFalse(result.is_approved)
        self.assertEqual(len(result.issues), 2)

    def test_response_review_model(self):
        # Test the ResponseReview model directly
        approved = ResponseReview(response="Good", is_approved=True)
        self.assertTrue(approved.is_approved)
        
        rejected = ResponseReview(
            response="Bad", 
            is_approved=False,
            issues=["Problem 1"]
        )
        self.assertFalse(rejected.is_approved)
        self.assertEqual(len(rejected.issues), 1)


if __name__ == '__main__':
    unittest.main()