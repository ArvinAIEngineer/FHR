import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import fitz  # PyMuPDF
from PIL import Image
import io
import base64
from datetime import datetime
import uuid

# LangChain imports
from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain_community.vectorstores import Chroma
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain.schema import Document
# from langchain_community.embeddings import OllamaEmbeddings
from langchain_ollama import OllamaEmbeddings
# from langchain_community.llms import Ollama
from langchain_ollama import OllamaLLM
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

os.environ['NO_PROXY'] = '10.254.115.17, 10.254.140.69'

class DocumentIngestionPipeline:
    def __init__(
        self,
        ollama_base_url: str = "http://10.254.140.69:11434",
        embedding_model: str = "nomic-embed-text:latest",
        ocr_model: str = "gemma3:27b",
        persist_directory: str = "./chroma_db_backup",
        images_directory: str = "./images",
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ):
        """
        Initialize the document ingestion pipeline
        
        Args:
            ollama_base_url: Base URL for Ollama server
            embedding_model: Embedding model name
            ocr_model: OCR/text extraction model name
            persist_directory: Directory to persist ChromaDB
            images_directory: Directory to save page images
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
        """
        self.ollama_base_url = ollama_base_url
        self.embedding_model = embedding_model
        self.ocr_model = ocr_model
        self.persist_directory = persist_directory
        self.images_directory = images_directory
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Create images directory if it doesn't exist
        Path(self.images_directory).mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.embeddings = OllamaEmbeddings(
            model=self.embedding_model,
            base_url=self.ollama_base_url
        )
        
        self.ocr_llm = OllamaLLM(
            model=self.ocr_model,
            base_url=self.ollama_base_url
        )
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )
        
        # Initialize or load existing vector store
        self.vector_store = self._initialize_vector_store()
        
    def _initialize_vector_store(self) -> Chroma:
        """Initialize ChromaDB vector store"""
        return Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings
        )
    
    def _extract_images_from_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract images from PDF for OCR processing"""
        images = []
        doc = fitz.open(pdf_path)
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            image_list = page.get_images(full=True)
            
            for img_index, img in enumerate(image_list):
                xref = img[0]
                pix = fitz.Pixmap(doc, xref)
                
                if pix.n - pix.alpha < 4:  # GRAY or RGB
                    img_data = pix.tobytes("png")
                    images.append({
                        "page": page_num,
                        "image_index": img_index,
                        "data": img_data
                    })
                pix = None
        
        doc.close()
        return images
    
    def _save_page_as_image(self, pdf_path: str, page_num: int, document_id: str) -> Optional[str]:
        """Save a PDF page as image file and return the file path"""
        try:
            doc = fitz.open(pdf_path)
            page = doc.load_page(page_num)
            pix = page.get_pixmap()
            img_data = pix.tobytes("png")
            doc.close()
            
            # Create filename with document ID and page number
            filename = f"{document_id}_page_{page_num + 1}.png"
            image_path = Path(self.images_directory) / filename
            
            # Save image to file
            with open(image_path, "wb") as img_file:
                img_file.write(img_data)
            
            return str(image_path)
        except Exception as e:
            logger.error(f"Error saving page {page_num} as image: {e}")
            return None
    
    def _ocr_image_with_llm(self, image_data: bytes) -> str:
        """Use Gemma3 model for OCR on images"""
        try:
            # Convert image to base64 for processing
            image_b64 = base64.b64encode(image_data).decode()
            
            prompt = """
            You are an OCR assistant that can read text from images in multiple languages including Arabic and English.
            Please extract all text from this image accurately, preserving the original structure and formatting as much as possible.
            If the image contains tables, preserve the table structure.
            If no text is found, return 'No text detected'.
            
            Image data: [BASE64_IMAGE_DATA]
            
            Extracted text:
            """
            prompt = prompt.replace("[BASE64_IMAGE_DATA]", image_b64)
            # Note: This is a simplified approach. In practice, you might need
            # to use a vision-language model that can process images directly
            response = self.ocr_llm.invoke(prompt)
            return response.strip()
        except Exception as e:
            logger.error(f"Error in OCR processing: {e}")
            return "OCR processing failed"
    
    def _process_scanned_pdf(self, pdf_path: str, document_id: str, document_name: str, processed_at: str) -> List[Document]:
        """Process scanned PDF using OCR"""
        logger.info(f"Processing scanned PDF: {pdf_path}")
        documents = []
        
        # Extract images from PDF
        images = self._extract_images_from_pdf(pdf_path)
        
        for img_info in images:
            ocr_text = self._ocr_image_with_llm(img_info["data"])
            if ocr_text and ocr_text != "No text detected":
                # Save page as image file for metadata
                page_image_path = self._save_page_as_image(pdf_path, img_info["page"], document_id)
                
                doc = Document(
                    page_content=ocr_text,
                    metadata={
                        "source": pdf_path,
                        "page": img_info["page"],
                        "type": "scanned_pdf_ocr",
                        "document_id": document_id,
                        "document_name": document_name,
                        "page_number": img_info["page"] + 1,  # 1-indexed page numbers
                        "page_image": page_image_path,
                        "processed_at": processed_at
                    }
                )
                documents.append(doc)
        
        return documents
    
    def _load_document(self, file_path: str) -> List[Document]:
        """Load document based on file type"""
        file_path = Path(file_path)
        file_extension = file_path.suffix.lower()
        
        # Generate document metadata
        document_id = str(uuid.uuid4())
        document_name = file_path.name
        processed_at = datetime.now().isoformat()
        
        try:
            if file_extension == '.pdf':
                # Try regular PDF loading first
                try:
                    loader = PyPDFLoader(str(file_path))
                    documents = loader.load()
                    
                    # Check if document seems to be scanned (low text content)
                    total_text = sum(len(doc.page_content) for doc in documents)
                    if total_text < 100:  # Threshold for considering as scanned
                        logger.info("Document appears to be scanned, using OCR")
                        documents = self._process_scanned_pdf(str(file_path), document_id, document_name, processed_at)
                    else:
                        # Add enhanced metadata to regular PDF documents
                        for i, doc in enumerate(documents):
                            page_num = doc.metadata.get("page", i)
                            page_image_path = self._save_page_as_image(str(file_path), page_num, document_id)
                            
                            doc.metadata.update({
                                "document_id": document_id,
                                "document_name": document_name,
                                "page_number": page_num + 1,  # 1-indexed page numbers
                                "page_image": page_image_path,
                                "processed_at": processed_at
                            })
                    
                    return documents
                except Exception as e:
                    logger.warning(f"Regular PDF loading failed: {e}, trying OCR")
                    return self._process_scanned_pdf(str(file_path), document_id, document_name, processed_at)
            
            elif file_extension in ['.docx', '.doc']:
                loader = Docx2txtLoader(str(file_path))
                documents = loader.load()
                
                # Add enhanced metadata to DOCX documents
                for doc in documents:
                    doc.metadata.update({
                        "document_id": document_id,
                        "document_name": document_name,
                        "page_number": 1,  # DOCX doesn't have clear page separation
                        "page_image": None,  # Not applicable for DOCX
                        "processed_at": processed_at
                    })
                
                return documents
            
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")
                
        except Exception as e:
            logger.error(f"Error loading document {file_path}: {e}")
            return []
    
    def ingest_documents(self, file_paths: List[str]) -> int:
        """
        Ingest multiple documents into the vector store
        
        Args:
            file_paths: List of paths to documents to ingest
            
        Returns:
            Number of chunks added to vector store
        """
        all_chunks = []
        
        for file_path in file_paths:
            logger.info(f"Processing file: {file_path}")
            
            # Load document
            documents = self._load_document(file_path)
            
            if not documents:
                logger.warning(f"No content extracted from {file_path}")
                continue
            
            # Split documents into chunks
            for doc in documents:
                chunks = self.text_splitter.split_documents([doc])
                
                # Add/update metadata for each chunk
                for chunk in chunks:
                    # Preserve existing enhanced metadata
                    chunk.metadata.update({
                        "source": file_path,
                        "file_name": Path(file_path).name,
                        # These will be preserved from the original document metadata:
                        "documentId": chunk.metadata.get("document_id"),
                        "documentName": chunk.metadata.get("document_name"),
                        "pageNumber": chunk.metadata.get("page_number"),
                        "page_image": chunk.metadata.get("page_image"),
                    })
                    
                    # Add processed_at time as string
                    date_str = chunk.metadata.get("processed_at")
                    if date_str:
                        chunk.metadata["processed_at_str"] = date_str
                
                all_chunks.extend(chunks)
        
        if all_chunks:
            # Add chunks to vector store
            logger.info(f"Adding {len(all_chunks)} chunks to vector store")
            self.vector_store.add_documents(all_chunks)
            # self.vector_store.persist()
            logger.info("Documents successfully ingested and persisted")
        
        return len(all_chunks)
    
    def ingest_single_document(self, file_path: str) -> int:
        """Ingest a single document"""
        return self.ingest_documents([file_path])
    
    def ingest_folder(self, folder_path: str, recursive: bool = True) -> int:
        """
        Ingest all supported documents from a folder
        
        Args:
            folder_path: Path to folder containing documents
            recursive: Whether to search subfolders recursively
            
        Returns:
            Number of chunks added to vector store
        """
        supported_extensions = {'.pdf', '.docx', '.doc'}
        file_paths = []
        
        folder_path = Path(folder_path)
        
        if not folder_path.exists():
            logger.error(f"Folder does not exist: {folder_path}")
            return 0
        
        if not folder_path.is_dir():
            logger.error(f"Path is not a directory: {folder_path}")
            return 0
        
        # Find all supported files
        if recursive:
            for ext in supported_extensions:
                file_paths.extend(folder_path.rglob(f"*{ext}"))
        else:
            for ext in supported_extensions:
                file_paths.extend(folder_path.glob(f"*{ext}"))
        
        # Convert to strings
        file_paths = [str(path) for path in file_paths]
        
        logger.info(f"Found {len(file_paths)} supported documents in {folder_path}")
        
        if not file_paths:
            logger.warning(f"No supported documents found in {folder_path}")
            return 0
        
        return self.ingest_documents(file_paths)
    
    def search_similar(self, query: str, k: int = 5) -> List[Document]:
        """Search for similar documents"""
        return self.vector_store.similarity_search(query, k=k)
    
    def search_with_score(self, query: str, k: int = 5) -> List[tuple]:
        """Search for similar documents with similarity scores"""
        return self.vector_store.similarity_search_with_score(query, k=k)
    
    def get_retriever(self, search_type: str = "similarity", k: int = 5):
        """Get a retriever for RAG applications"""
        return self.vector_store.as_retriever(
            search_type=search_type,
            search_kwargs={"k": k}
        )


# Example usage
if __name__ == "__main__":
    # Initialize pipeline
    pipeline = DocumentIngestionPipeline(
        ollama_base_url="http://10.254.140.69:11434",  # Change if Ollama is on different server
        persist_directory="./multilingual_chroma_db4",
        images_directory="./images"  # Directory where page images will be saved
    )
    
    # Example 1: Ingest from folder
    documents_folder = "./docs"
    
    try:
        num_chunks = pipeline.ingest_folder(documents_folder, recursive=True)
        print(f"Successfully ingested {num_chunks} chunks from folder")
    except Exception as e:
        print(f"Error during folder ingestion: {e}")
    
    # Example 2: Ingest specific documents
    # document_paths = [
    #     "path/to/your/document1.pdf",
    #     "path/to/your/document2.docx",
    # ]
    
    # try:
    #     num_chunks = pipeline.ingest_documents(document_paths)
    #     print(f"Successfully ingested {num_chunks} chunks from specific files")
    # except Exception as e:
    #     print(f"Error during document ingestion: {e}")
    
    # Example 3: Search with enhanced metadata
    # results = pipeline.search_similar("your search query")
    # for doc in results:
    #     print(f"Document: {doc.metadata.get('documentName')}")
    #     print(f"Page: {doc.metadata.get('pageNumber')}")
    #     print(f"Document ID: {doc.metadata.get('documentId')}")
    #     print(f"Page image path: {doc.metadata.get('page_image')}")
    #     print(f"Processed at: {doc.metadata.get('processed_at_str')}")
    #     print("---")