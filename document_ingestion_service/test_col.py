from chromadb.config import Settings
from core.config import settings
from langchain_ollama import OllamaEmbeddings
from langchain_core.embeddings import Embeddings
from langchain_chroma import Chroma

# Initialize embedding model
embeddings: Embeddings = OllamaEmbeddings(
    model=settings["ollama_embedding_model"],
    base_url=settings["ollama_base_url"]
)

# Initialize LangChain Chroma vectorstore
chroma_client = Chroma(
    persist_directory=settings["vectorstore_persist_directory"],
    embedding_function=embeddings,
    collection_name=settings["vectorstore_collection_name"]
)

# Count the number of chunks in the collection
chunk_count = chroma_client._collection.count()

print(f"Total number of chunks in collection '{settings['vectorstore_collection_name']}': {chunk_count}")


# Get all stored chunks along with their metadata
all_chunks = chroma_client._collection.get(include=["metadatas"])

# Extract metadata from all chunks
metadatas = all_chunks["metadatas"]

# Collect all document names
document_names = [meta.get("document_name") for meta in metadatas if meta.get("document_name")]

# Deduplicate to get unique documents
unique_document_names = list(set(document_names))

print(f"Total chunks: {len(metadatas)}")
print(f"Total unique documents: {len(unique_document_names)}")

print("Document Names:")
for name in unique_document_names:
    print(f"- {name}")
