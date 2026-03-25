from abc import ABC, abstractmethod
from typing import List
from langchain_core.documents import Document

class BaseEmbedding():
    """
    Interface for embedding handlers that work with LangChain Document objects.
    """

    @abstractmethod
    async def load_model(self) -> None:
        """
        Load or initialize the embedding model.
        """
        pass

    @abstractmethod
    async def embed_documents(self, documents: List[Document]) -> List[List[float]]:
        """
        Generate embeddings for a list of LangChain Document objects.
        """
        pass

    @abstractmethod
    async def store_documents(self, documents: List[Document]) -> None:
        """
        Store documents and their embeddings in the vector store.
        """
        pass
        
    @abstractmethod
    async def retrieve_documents(self, query: str, top_k: int = 5) -> List[Document]:
        """
        Retrieve relevant documents based on a query.
        """
        pass
