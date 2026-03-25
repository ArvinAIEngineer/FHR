import yaml
from api import VectorstoreConnector
from utils.logger import get_logger
import logging
from langchain.retrievers import EnsembleRetriever
# LangChain Community & Extended Imports
from langchain_community.retrievers import BM25Retriever
from langchain.schema import Document
from dateutil.parser import parse
from datetime import timezone
from sentence_transformers import CrossEncoder



class ChromaRetriever:
    def __init__(
        self,
        top_k: int = 10,
        similarity_cutoff: float = 0,
        vectorstore_config_path: str = "./configs/vectorstore_config.yaml",
        rag_config_path: str = "./configs/rag_workflow_config.yaml"

    ):
        """
        Initialize the retriever using the vectorstore defined in vectorstore.py.
        The vectorstore connector will attempt a remote connection first;
        if that fails, it will fall back to a local Chroma database.
        """
        self.top_k = top_k
        self.similarity_cutoff = similarity_cutoff
        self.logger = get_logger()
        self.logger.setLevel(logging.INFO)

        # Load configuration
        with open(rag_config_path, "r") as file:
            config = yaml.safe_load(file)
            self.retrieval_config = config.get("retrieval_config", {})  # Fixed typo: "retrival_config" -> "retrieval_config"

        # Initialize the vectorstore via the connector
        self.connector = VectorstoreConnector(config_path=vectorstore_config_path)
        self.vectorstore = self.connector.get_vectorstore()
        if self.vectorstore is None:
            raise Exception("Unable to initialize vectorstore.")

         # Initialize reranker model
        if self.retrieval_config.get("use_reranker", False):
            reranker_model_name = self.retrieval_config.get("reranker", "BAAI/bge-reranker-v2-m3")  # Fixed typo: "rereanker" -> "reranker"
            self.reranker = CrossEncoder(reranker_model_name)
            self.logger.info(f"Initialized Reranker {reranker_model_name} successfully")

        # Initialize BM25 retriever if enabled
        self.bm25_retriever = None
        if self.retrieval_config.get("enable_bm25_ensemble", False):
            try:
                collection = self.vectorstore._collection
                all_docs = collection.get(
                    include=["documents", "metadatas"],
                    limit=self.retrieval_config.get("bm25_retrieval_doc_limit", 1000)
                )

                docs = [
                    Document(page_content=doc, metadata=meta)
                    for doc, meta in zip(all_docs["documents"], all_docs["metadatas"])
                    if doc and doc.strip()  # Filter out empty documents
                ]

                if docs:
                    self.bm25_retriever = BM25Retriever.from_documents(docs)
                    # Configure BM25 retriever
                    bm25_k = self.retrieval_config.get("bm25_top_k", self.retrieval_config.get("top_k", 5) * 2)
                    self.bm25_retriever.k = bm25_k
                    self.logger.info(f"[BM25 Init] Loaded {len(docs)} documents for BM25Retriever (k={bm25_k})")
                else:
                    self.logger.warning(f"[BM25 Init] No valid documents found in collection")
            except Exception as e:
                self.logger.error(f"Failed to initialize BM25 retriever: {e}")
                self.bm25_retriever = None

    def format_docs(self,docs):
        formatted = []
        for doc in docs:
            metadata = doc.metadata
            formatted.append({
                "chunkText": doc.page_content,
                "metadata": {
                    "documentId": metadata.get("document_id"),
                    "documentName": metadata.get("document_name"),
                    "pageNumber": str(metadata.get("page_number")),
                    "screenshotUrl": metadata.get("page_image"),
                }
            })
        return formatted
    
    def retrieve_content_from_vector(self, query, fallback_attempts=3):
        """Enhanced retrieval with multiple fallback strategies."""
        
        # Try different retrieval strategies
        strategies = [
            {"k": self.retrieval_config.get("top_k", 5)},  # Normal retrieval
            # {"k": self.retrieval_config.get("top_k", 3) * 2},  # Double the results
            # {"k": 10},  # Even more results
        ]
        
        for attempt, strategy in enumerate(strategies):
            self.logger.info(f"Retrieval attempt {attempt + 1} with strategy: {strategy}")
            
            dense = self.vectorstore.as_retriever(search_kwargs=strategy)
            
            if self.bm25_retriever is None:
                self.logger.info("Using Dense retrieval")
                results = dense.invoke(query)
            else:
                self.logger.info("Using Hybrid retrieval")
                bm25_weight = self.retrieval_config.get("bm25_retrieval_weight", 0.3)
                dense_weight = 1.0 - bm25_weight
                self.logger.info(f"Hybrid retrieval weights - Dense: {dense_weight:.2f}, BM25: {bm25_weight:.2f}")
                hybrid = EnsembleRetriever(
                    retrievers=[dense, self.bm25_retriever], 
                    weights=[dense_weight, bm25_weight]
                )
                results = hybrid.invoke(query)

            # If we got results, process them
            if results:
                valid_docs = []
                for doc in results:
                    # Skip empty documents
                    if not doc.page_content or not doc.page_content.strip():
                        continue
                        
                    date_str = doc.metadata.get("processed_at")
                    if date_str:
                        try:
                            processed_date = parse(date_str)
                            if processed_date.tzinfo is None:
                                processed_date = processed_date.replace(tzinfo=timezone.utc)
                            valid_docs.append(doc)
                        except Exception as e:
                            self.logger.warning(f"Invalid processed_at format: {date_str} — skipping doc")

                if valid_docs:
                    # Apply reranking if enabled
                    if self.retrieval_config.get("use_reranker", False):
                        doc_pairs = [(query, doc.page_content) for doc in valid_docs]
                        scores = self.reranker.predict(doc_pairs)
                        reranked = sorted(zip(valid_docs, scores), key=lambda x: x[1], reverse=True)
                        top_n = self.retrieval_config.get("top_k", 5)
                        top_docs = [doc for doc, _ in reranked[:top_n]]
                        return self.format_docs(top_docs)
                    
                    return self.format_docs(valid_docs)
        
        # If all strategies failed, log error and return empty (or raise exception)
        self.logger.error(f"All retrieval strategies failed for query: {query}")
        return []
    
    def query(self, query: str) -> dict:
        """Fetch relevant context from the vector store based on the user's query."""
        self.logger.info(f"Retrieving context for query: {query}")
        results = self.retrieve_content_from_vector(query)
        filtered_results = []
        if not results:
            self.logger.info("No relevant documents found.")
            return []

        for doc in results:
            filtered_results.append((doc["chunkText"], doc["metadata"]))
        return filtered_results

    def get_retrieval_stats(self) -> dict:
        """Get statistics about the retrieval setup."""
        return {
            "hybrid_enabled": self.bm25_retriever is not None,
            "reranker_enabled": self.retrieval_config.get("use_reranker", False),
            "bm25_weight": self.retrieval_config.get("bm25_retrieval_weight", 0.3),
            "top_k": self.retrieval_config.get("top_k", 5),
            "vectorstore_type": type(self.vectorstore).__name__
        }
        
    # def query(self, question: str) -> list:
    #     """
    #     Retrieve documents for the given query text.

    #     This method uses a similarity search with score filtering. It calls the
    #     vectorstore’s similarity_search_with_score function (if available) to get a 
    #     list of (document, score) tuples. Documents with a score greater than the 
    #     similarity_cutoff are filtered out. The remaining documents are then returned 
    #     as a list of tuples in the format: (document_content, document_metadata).
    #     """
    #     try:
    #         # Try to get documents with score information
    #         results = self.vectorstore.similarity_search_with_score(question, k=self.top_k)
    #         self.logger.info(f"RAGworkflow: initial results: {results}")
    #     except Exception:
    #         # Fallback: if the vectorstore does not support scores, use similarity_search.
    #         docs = self.vectorstore.similarity_search(question, k=self.top_k)
    #         # In this case, we assume no scores and include all returned docs.
    #         results = [(doc, None) for doc in docs]
        
    #     filtered_results = []
    #     for doc, score in results:
    #         # If there is no score (or score is None), add document; otherwise, only add if score is below threshold.
    #         # if score is None or score <= self.similarity_cutoff:
    #         if True:
    #             filtered_results.append((doc.page_content, doc.metadata))
    #     self.logger.info(f"RAGworkflow: filtered_results: {filtered_results}")
    #     return filtered_results


# Example usage
if __name__ == "__main__":
    retriever = ChromaRetriever()
    results = retriever.query("leave")
    
    print("\n--- Retrieved Results ---")
    for i, (content, metadata) in enumerate(results, 1):
        print(f"\nResult {i}:\nContent: {content}\nMetadata: {metadata}\n")
