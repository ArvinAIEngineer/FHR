import os
import logging
from typing import List, Dict, Any
from langchain_chroma import Chroma
from langchain_openai import AzureOpenAIEmbeddings
from langchain_ollama import OllamaEmbeddings
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from core.config import settings
import json

logger = logging.getLogger(__name__)
os.environ['NO_PROXY'] = '10.254.140.69'

class VectorStoreManager:
    """
    Manages document storage and retrieval using Chroma and Azure OpenAI embeddings.
    """

    def __init__(self):
        # Initialize embeddings
        if settings.get("use_ollama", True):
            self.embeddings: Embeddings = OllamaEmbeddings(
                model=settings["ollama_embedding_model"],
                base_url=settings["ollama_base_url"],
                num_ctx=settings["num_ctx"]  
            )
        else:
            self.embeddings: Embeddings = AzureOpenAIEmbeddings(
                azure_deployment=settings["azure_openai_embedding_deployment"],
                openai_api_version=settings["azure_openai_api_version"],
                azure_endpoint=settings["azure_openai_endpoint"],
                api_key=settings["azure_openai_api_key"]
            )

        # Initialize Chroma vector store
        self.vector_store = Chroma(
            persist_directory=settings["vectorstore_persist_directory"],
            embedding_function=self.embeddings,
            collection_name=settings["vectorstore_collection_name"]
        )

        # Initialize retriever
        self.retriever = self.vector_store.as_retriever()

    def stringify_complex_metadata(self, metadata: dict) -> dict:
        flat_metadata = {}
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, bool)) or value is None:
                flat_metadata[key] = value
            else:
                # Convert list/dict/other complex types to JSON string
                try:
                    flat_metadata[key] = json.dumps(value)
                except Exception:
                    flat_metadata[key] = str(value)  # fallback
        return flat_metadata

    def store_documents(self, chunks: List[Dict[str, Any]]) -> None:
        """
        Store document chunks in the vector store.

        Args:
            chunks: List of document chunks with metadata
        """
        try:
            # Convert chunks to Langchain Document format
            documents = []
            for chunk in chunks:
                doc = Document(
                    page_content=chunk["text"],
                    metadata=self.stringify_complex_metadata(chunk["metadata"])
                )
                documents.append(doc)

            # Add documents to vector store and get their IDs
            inserted_ids = self.vector_store.add_documents(documents)
            logger.info(f"Stored {len(documents)} document chunks in vector store with IDs: {inserted_ids}")
            return inserted_ids  # Return the list of IDs

        except Exception as e:
            logger.error(f"Error storing documents in vector store: {str(e)}")
            # Optionally return an empty list or re-raise depending on desired error handling
            # For now, re-raising to signal failure clearly.
            raise

    def search_documents(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for relevant documents using the vector store.

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            List of relevant documents with scores
        """
        try:
            # Search for relevant documents
            results = self.retriever.get_relevant_documents(query)

            # Format results
            formatted_results = []
            for doc in results:
                formatted_results.append({
                    "text": doc.page_content,
                    "metadata": doc.metadata,
                    "score": doc.metadata.get("score", 0.0)
                })

            return formatted_results

        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            return []

    def document_exists(self, doc_id: str) -> bool:
        """Check if a document with given ID exists in the vector store"""
        try:
            results = self.vector_store.get(
                where={"document_id": {"$eq": doc_id}},
                limit=1
            )
            return len(results['ids']) > 0
        except Exception as e:
            logger.error(f"Error checking document existence {doc_id}: {str(e)}")
            return False

    def get_document_by_id(self, doc_id: str) -> Dict[str, Any]:
        """
        Retrieve a specific document by its ID.

        Args:
            doc_id: Document ID

        Returns:
            Document with metadata
        """
        try:
            # Search for document by ID
            results = self.vector_store.similarity_search_with_score(
                f"document_id:{doc_id}",
                k=1
            )

            if results:
                doc, score = results[0]
                return {
                    "text": doc.page_content,
                    "metadata": doc.metadata,
                    "score": score
                }
            return None

        except Exception as e:
            logger.error(f"Error retrieving document {doc_id}: {str(e)}")
            return None

    def find_similar_chunks_by_uuid(self, query_uuid: str, query_document_id: str, similarity_threshold: float = 0.8, k: int = 1000) -> List[Dict[str, Any]]:
        logger.info("VectorStoreManager logger is working")

        """
        Find chunks similar to a given chunk UUID, excluding chunks from the same document.

        Args:
            query_uuid: The UUID of the chunk to find similar items for.
            query_document_id: The document ID of the query chunk, to exclude matches from the same document.
            similarity_threshold: The minimum cosine similarity score for a chunk to be considered similar (default: 0.8).
            k: The number of initial candidates to retrieve (default: 5).

        Returns:
            A list of dictionaries, each containing the similar chunk's UUID, metadata, and similarity score.
        """
        try:
            query_result = self.vector_store.get(ids=[query_uuid], include=["embeddings"])
            if query_result is None or "embeddings" not in query_result or len(query_result["embeddings"]) == 0:
                logger.warning(f"Could not retrieve embedding for query UUID: {query_uuid}")
                return []
            query_embedding = query_result["embeddings"][0]
            logger.info(f"Query UUID: {query_uuid}, Type: {type(query_uuid)}")
            logger.info(f"Query Document ID: {query_document_id}, Type: {type(query_document_id)}")

            distance_threshold = 1.0 - similarity_threshold

            where_filter = {
                "$and": [
                    {"id": {"$ne": query_uuid}},  # Exclude the query chunk itself by its Chroma ID (usually the UUID)
                    {"document_id": {"$ne": query_document_id}}  # Exclude chunks from the same document
                ]
            }

            logger.info(f"Where filter: {json.dumps(where_filter)}")

            results = self.vector_store._collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                where=where_filter,
                include=["documents", "metadatas", "distances"]
            )
            logger.info(f"Similar results{results}")

            similar_chunks = []
            for doc_id, doc_metadata, distance in zip(
                    results["ids"][0], results["metadatas"][0], results["distances"][0]
            ):
                if distance <= distance_threshold:
                    similarity = 1.0 - distance
                    metadata = doc_metadata
                    # Ensure metadata is properly deserialized if it was stringified
                    if isinstance(metadata, dict):
                        for key, value in metadata.items():
                            if isinstance(value, str):
                                try:
                                    if (value.startswith('{') and value.endswith('}')) or \
                                       (value.startswith('[') and value.endswith(']')):
                                        metadata[key] = json.loads(value)
                                except json.JSONDecodeError:
                                    pass # Not a JSON string, keep as is

                    similar_chunks.append({
                        "similar_chunk_chroma_id": doc_id,
                        "similar_document_id": metadata.get("document_id"),
                        "metadata": metadata,
                        "similarity_score": similarity
                    })

            logger.info(f"Found {len(similar_chunks)} chunks similar to {query_uuid} (threshold: {similarity_threshold})")
            return similar_chunks

        except Exception as e:
            logger.error(f"Error finding similar chunks for UUID {query_uuid}: {str(e)}")
            return []
