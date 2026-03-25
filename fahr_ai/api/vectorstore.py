import sys
sys.path.append("../utils/")

import requests
from typing import Optional, List, Dict, Any
from langchain.vectorstores import VectorStore
import yaml
from chromadb import PersistentClient
from langchain_ollama import OllamaEmbeddings
from utils.logger import get_logger
import logging

class RemoteVectorstore(VectorStore):
    """
    A vectorstore implementation that connects to a remote vectorstore API.
    This allows using the remote vectorstore with the same interface as a local one.
    """

    def __init__(self, endpoint: str):
        """
        Initialize the remote vectorstore.

        Args:
            endpoint (str): URL endpoint for the vectorstore API
        """
        self.logger = get_logger()
        self.logger.setLevel(logging.INFO)
        self.logger.info("Initializing Remote Vectrstore")
        self.endpoint = endpoint

    def as_retriever(self, search_type="similarity", search_kwargs=None, **kwargs):
        """Create a retriever from the vectorstore."""
        from langchain.retrievers import VectorStoreRetriever

        if search_kwargs is None:
            search_kwargs = {}

        return VectorStoreRetriever(
            vectorstore=self,
            search_type=search_type,
            search_kwargs=search_kwargs,
            **kwargs
        )


class VectorstoreConnector:
    """
    Connector that provides unified access to remote or local vectorstores
    with automatic fallback capability
    """

    def __init__(self,
                 config_path="./configs/vectorstore_config.yaml",
                 ):
        """
        Initialize the VectorstoreConnector.

        Args:
            config_path (str): Path to the vectorstore config file. Default is "./configs/vectorstore_config.yaml".
        """
        self.logger = get_logger()
        self.logger.setLevel(logging.INFO)
        with open(config_path, "r") as config_file:
            self.config = yaml.safe_load(config_file)["vectorstore"]

        self.remote_endpoint = self.config["remote"]["endpoint"]
        self.local_persist_dir = self.config["local"]["persist_directory"]
        self.collection_name = self.config["local"]["collection_name"]
        self.embedding_model_name = self.config["local"]["embedding_model"]
        self.use_ollama=self.config["local"]["use_ollama"]
        self.vectorstore = None
        self.is_remote = False

        # Initialize the vectorstore - first try remote, then local
        self.logger.info("Initializing Vectrstore")
        self._initialize_vectorstore()

    def _initialize_vectorstore(self) -> None:
        """Initialize either remote or local vectorstore"""
        if self._try_remote_connection():
            self.logger.info("Successfully connected to remote vectorstore.")
            self.is_remote = True
            self.vectorstore = RemoteVectorstore(self.remote_endpoint)
        else:
            self.logger.info("Remote vectorstore unavailable. Falling back to local.")
            self._initialize_local_vectorstore()

    def _try_remote_connection(self) -> bool:
        return False
        """Test connection to remote vectorstore"""
        try:
            # Extract the base URL without the endpoint path
            base_url = self.remote_endpoint.rsplit('/', 1)[0]
            health_endpoint = f"{base_url}/health"

            # Send a health check request
            response = requests.get(
                health_endpoint,
                timeout=5
            )
            self.logger.info(f"Remote vectorstore health check: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Remote vectorstore connection failed: {e}")
            return False

    def _initialize_local_vectorstore(self) -> None:
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
            from langchain_chroma import Chroma
            if  self.use_ollama == True:
                embedding = OllamaEmbeddings(
                    model=self.config["local"]["ollama_embedding_model"],
                    base_url=self.config["local"]["ollama_base_url"]
                )
            else:
                embedding = HuggingFaceEmbeddings(model_name=self.embedding_model_name)
            


            self.vectorstore = Chroma(
                    collection_name=self.collection_name,
                    persist_directory=self.local_persist_dir,
                    embedding_function=embedding,
                )
            self.logger.info("Local vectorstore loaded successfully.")

            self.logger.info(f"Collection Name: {self.collection_name}")
            self.logger.info(f"Persist Directory: {self.local_persist_dir}")

            # Use PersistentClient to list collections and document counts
            client = PersistentClient(path=self.local_persist_dir)
            collections = client.list_collections()
            
            self.logger.info(f"[ChromaDB] Found {len(collections)} collections:")
            for coll in collections:
                self.logger.info(f"Collection Name: {coll.name}, Documents: {coll.count()}")

            # # NEW CODE (Chroma v0.6.0+ compatible):
            # collection_names = client.list_collections()  # Now returns list of strings
            # print(f"[ChromaDB] Found {len(collection_names)} collections:")
            # for collection_name in collection_names:
            #     try:
            #         collection = client.get_collection(name=collection_name)
            #         doc_count = collection.count()
            #         print(f"  - Collection Name: {collection_name}, Documents: {doc_count}")
            #     except Exception as e:
            #         print(f"  - Collection Name: {collection_name}, Documents: Error - {e}")
        except Exception as e:
            self.logger.error(f"Error loading local vectorstore: {e}")
            self.vectorstore = None

    def get_vectorstore(self) -> Optional[VectorStore]:
        """Get the vectorstore (either remote or local)"""
        return self.vectorstore