import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import asyncio

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    force=True  # <-- this line ensures it overrides existing loggers
)
import pytest
import pytest_asyncio
from langchain_core.messages import HumanMessage, AIMessage
from AIAgents.LegalAgent import LegalAgent
from langchain_ollama import ChatOllama
from AIAgents.base_agent import GraphState

@pytest_asyncio.fixture(scope="module")
async def hr_agent():
    llm = ChatOllama(model="gemma3", temperature=0)
    return LegalAgent(llm_model=llm)


@pytest.mark.asyncio
async def test_salary_query(hr_agent):
    # query = "Can I know my allowances and bonuses according to the law?"
    query = "explain whats the update in law number 17 from year 1976 about salary"
    state = GraphState(
        messages=[HumanMessage(content=query)],
        memory={},
        suggestions=[]
    )

    response = await hr_agent.run(state)
    logging.info(f"AGENT RESPONSE in pytest: {response}")
    # assert isinstance(response, str)
    # assert "leave balance" in response.lower()
    # assert "2019" in respons


    # Extract final AI response message
    ai_messages = [msg for msg in response["messages"] if isinstance(msg, AIMessage)]
    assert ai_messages, "No AI response found"
    final_answer = ai_messages[-1].content

    # Perform meaningful checks
    assert "law number 17" in final_answer.lower()
    # assert "2019" in final_answer


# @pytest.mark.asyncio
# async def test_arabic_query(hr_agent):
#     # query = "Can I know my allowances and bonuses according to the law?"
#     query = "Can a government employee still receive housing allowance if given official housing?"
#     state = GraphState(
#         messages=[HumanMessage(content=query)],
#         memory={},
#         suggestions=[]
#     )
#
#     response = await hr_agent.run(state)
#     logging.info(f"AGENT RESPONSE in pytest: {response}")
#     # assert isinstance(response, str)
#     # assert "leave balance" in response.lower()
#     # assert "2019" in respons
#
#
#     # Extract final AI response message
#     ai_messages = [msg for msg in response["messages"] if isinstance(msg, AIMessage)]
#     assert ai_messages, "No AI response found"
#     final_answer = ai_messages[-1].content
#
#     # Perform meaningful checks
#     assert "بدل السكن" in final_answer.lower()
#     # assert "2019" in final_answer
#
#
# @pytest.mark.asyncio
# async def test_leave_balance_query_notfound(hr_agent):
#     query = "Am i elgible for free food"
#     state = GraphState(
#         messages=[HumanMessage(content=query)],
#         memory={},
#         suggestions=[]
#     )
#
#     response = await hr_agent.run(state)
#     logging.info(f"AGENT RESPONSE in pytest: {response}")
#     # assert isinstance(response, str)
#     # assert "leave balance" in response.lower()
#     # assert "2019" in respons
#
#
#     # Extract final AI response message
#     ai_messages = [msg for msg in response["messages"] if isinstance(msg, AIMessage)]
#     assert ai_messages, "No AI response found"
#     final_answer = ai_messages[-1].content
#
#     # Perform meaningful checks
#     assert "couldn't find a reliable answer" in final_answer.lower()
#
#
# @pytest.mark.asyncio
# async def test_query_refinement_with_history(hr_agent):
#     # Simulate previous conversation turns
#     history = [
#         HumanMessage(content="What are the latest employee benefits updates?"),
#         AIMessage(content="The latest updates include extended parental leave and hybrid work policy."),
#         HumanMessage(content="How does this affect housing allowance?")
#     ]
#
#     # New follow-up query (ambiguous unless history is considered)
#     current_query = "How does this resolution affect newly hired employees?"
#
#     # Build the full message history (history + current user query)
#     state = GraphState(
#         messages=history + [HumanMessage(content=current_query)],
#         memory={},
#         suggestions=[]
#     )
#
#     response = await hr_agent.run(state)
#     logging.info(f"AGENT RESPONSE with history: {response}")
#
#     # Check response contains contextually relevant details
#     ai_messages = [msg for msg in response["messages"] if isinstance(msg, AIMessage)]
#     assert ai_messages, "No AI response found"
#     final_answer = ai_messages[-1].content
#
#     # Depending on what you expect, assert something like:
#     assert "newly hired" in final_answer.lower()
#     # You could also assert that it does not default to generic answer