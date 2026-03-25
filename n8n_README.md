## 1. Prerequisites
Before running the workflow, ensure you have the following installed on your system:
- n8n: The workflow is designed for n8n (version 1.x or higher).
- Docker (Optional but recommended): For running Qdrant and Ollama locally.

## 2. External Services & API Keys
This workflow relies on several external integrations. You will need valid credentials for:
- Azure OpenAI: Used for the primary LLM nodes (Guardrails, Virtual Agent, Reviewer).
- Qdrant: A vector database instance (Cloud or Local) with a collection named (`fahr`).
- Ollama: Used for local embeddings (`Qwen3-Embedding-8B`).
- Cohere: Required for the Reranker node (`rerank-multilingual-v3.0`).

## 3. Installation Requirements
If you are running n8n via npm or in a custom environment, you must ensure the LangChain dependencies are available. Create a requirements.txt file (though n8n usually handles these via its internal package manager or UI-based community nodes, these are the logical dependencies used):
**requirements.txt**
``` text
n8n-nodes-base
@n8n/n8n-nodes-langchain
qdrant-client
cohere-ai
openai
```

## 4. Workflow Configuration
1. Import the Workflow: Import the `AI Orchestrator Workflow.json` into your n8n instance.
2. Credentials:
   - Set up Azure OpenAI API credentials.
   - Set up Qdrant API credentials.
   - Set up Ollama API credentials (point to your local or remote Ollama instance).
   - Set up Cohere API credentials.
3. Environment Variables: Ensure your n8n instance allows the use of the Code node if you are performing advanced data normalization.


## 5. Usage Notes
- Entry Points: The workflow starts via a Webhook (`api/Conversations/Conversation`) or the Chat Trigger.
- Data Ingestion: Use the Form Trigger ("Upload your file here") to upload PDFs or CSVs to populate the Qdrant vector store before testing RAG queries.