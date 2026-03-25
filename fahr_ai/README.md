# FAHR_AI

## Overview
FAHR_AI is a modular AI system designed to perform core Natural Language Processing (NLP) tasks such as:
- Named Entity Recognition (NER)
- Context Compression
- Topic Modeling
- Document Language Identification

Additionally, a mock demonstration of workflows (such as intents, data validation, and login management) is included to showcase the system's capabilities.

---

## Repository Structure
```
fahr_ai/
├── api/
│   ├── __init__.py
│   ├── main.py                      # FastAPI entry point
│   ├── chat.py                      # Chat endpoints
│   ├── document.py                  # Document processing endpoints
│   └── health.py                    # Health check endpoint
├── orchestrator/                    # Orchestration layer
│   ├── __init__.py
│   └── orchestrator.py             # Main orchestrator class
├── workflows/                      # Complex task workflows
│   ├── __init__.py
│   ├── base_workflow.py            # Abstract workflow class
│   ├── legal_assistant.py          # Legal domain workflow
│   ├── hr_assistant.py             # HR domain workflow 
│   └── general_assistant.py        # Default workflow
├── agents/                         # Individual specialized agents
│   ├── __init__.py
│   ├── base_agent.py               # Abstract agent class
│   ├── rag_agent.py                # Standard RAG agent 
│   ├── corrective_rag_agent.py     # RAG with corrections
│   └── web_search_agent.py         # Web search agent
├── embeddings/                     # Embedding models 
│   ├── arabic_embedding.py         # For arabic language
│   ├── english_embedding.py        # For english language
│   └── multilingual_embedding.py   # multilingual
├── llm/                            # LLM interfaces
│   ├── ollama_inference.py      
│   └── hf_inference.py          
├── document_processing/            # Document handling
│   └──pdf_parser.py
├── configs/                        # add your configs files here
├── db/                             # Database interfaces
├── utils/                          # Utility functions
├── Dockerfile
├── requirements.txt
└── README.md
```

# FAHR Document Processing API

A FastAPI service for processing PDF documents, extracting text, images, and tables, and storing them in a vector database.

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd fahr_ai
```

2. Create a virtual environment (optional but recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure the service:
- Copy `document_processing/config/config.yaml.example` to `document_processing/config/config.yaml`
- Update the Azure OpenAI settings in the config file with your credentials

## Running the Service

1. Start the FastAPI server:
```bash
uvicorn document_processing.service.api:app --host 0.0.0.0 --port 8000
```

2. The service will be available at `http://localhost:8000`

## API Usage

### Process PDF Documents

Send a POST request to process PDF documents:

```bash
curl -X POST "http://localhost:8000/process" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "files=@/path/to/your/document.pdf" \
  -F "document_type=general" \
  -F "dpi=600"
```

Parameters:
- `files`: PDF file(s) to process (required)
- `document_type`: Type of document (default: "general")
- `dpi`: DPI for image extraction (default: 600)

### Health Check

Check the service status:
```bash
curl "http://localhost:8000/health"
```

## Features

- PDF text extraction
- Page image capture (BASE64)
- Table extraction (HTML and text format)
- Language detection
- Content summarization
- Vector storage for semantic search

## Response Format

The API returns a JSON response with:
- Processed text content
- Page images in BASE64 format
- Extracted tables in HTML format
- Document metadata
- Vector store chunks
