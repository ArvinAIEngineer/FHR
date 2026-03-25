import asyncio
from api.mock_crm_client import MockCRMClient
from AIAgents.CRMAgent import CRMAgent
from langchain_ollama import ChatOllama


async def test_crm_summarizer():
    crm_client = MockCRMClient()
    llm = ChatOllama(
    model="llama2:13b",  # or "llama3:instruct" depending on your Ollama tag
    temperature=0.1)   
    summarizer = CRMAgent(crm_client, llm)

    initial_state = {
        "username": "FAHR552615",
        "textMessage": "Can you give me an update on my tickets?"
    }

    result = await summarizer.run_with_mock(initial_state)

    print("\n Open Ticket Summaries:")
    for k, v in result["open_ticket_summaries"].items():
        print(f"\n Ticket ID: {k}")
        print(f"Summary: {v['summary']}")
        print(f"Details: {v['details']}")
        print(f"Comments: {v['comments']}")

    print("\n Closed Ticket Info:")
    for t in result["closed_ticket_info"]:
        print(f"\n Ticket ID: {t['CRM_Case_Number']}")
        print(f"Resolution: {t.get('ResolutionRemarks', 'N/A')}")
        print(f"Details: {t}")


def main():
    asyncio.run(test_crm_summarizer())


if __name__ == "__main__":
    main()