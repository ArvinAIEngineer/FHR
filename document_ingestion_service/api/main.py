from typing import List
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime
from pathlib import Path
import urllib.parse
import base64
import chromadb
import os
os.environ['NO_PROXY'] = '10.254.140.69'

from core.config import settings
from core.ingestion_pipeline import IngestionPipeline
from utils.file_ops import (
    create_processing_directory,
    save_uploaded_files,
    cleanup_directory
)
from utils.validation import validate_file_type
from utils.logger import get_logger
from utils.chroma_utils import ensure_ollama_chroma_collection

logger = get_logger(__name__)

ensure_ollama_chroma_collection(
    persist_dir=settings["vectorstore_persist_directory"],
    collection_name=settings["vectorstore_collection_name"],
    expected_dim=768
)

app = FastAPI(title="Document Ingestion Service", version="1.0.0",root_path="/ingest")

# Mount static image folder
app.mount("/download", StaticFiles(directory="images"), name="download")

# Initialize ingestion pipeline
pipeline = IngestionPipeline()


@app.post("/process")
async def process_documents(
    files: List[UploadFile] = File(...),
    document_type: str = "general",
    dpi: int = 600,
    session_token: str = None
):
    """
    Process uploaded PDF documents and create chunks for vector storage.
    """
    processing_dir = None
    try:
        # Validate files
        for file in files:
            if not validate_file_type(file.filename, [".pdf", ".docx", ".doc"]):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid file type: {file.filename}. Only PDF, DOCX, and DOC files are supported."
                )

        # Create processing directory
        processing_dir = create_processing_directory()

        # Save uploaded files
        saved_files = save_uploaded_files(files, processing_dir)

        # Process documents
        all_processed_data = []
        # all_chunks = []
        skipped_files = []
        for file_path in saved_files:
            logger.info(f"Processing document: {file_path}")
            try:
                result = pipeline.process_document(file_path)
                logger.info(f"Successfully processed document: {file_path}")
            except Exception as e:
                logger.error(f"Failed to process document {file_path}: {str(e)}")
                raise

            if "message" in result and result["message"] == "Document already processed":
                logger.info(f"Skipped duplicate: {file_path}")
                skipped_files.append({
                    "document_name": result.get("document_name"),
                    "document_id": result.get("document_id"),
                    "reason": result["message"]
                })
                continue

            all_processed_data.extend(result["processed_data"])
            # all_chunks.extend(result["processed_data"])

        # Build response
        response_data = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "document_type": document_type,
            "total_files": len(saved_files),
            "processed_files": len(saved_files) - len(skipped_files),
            # "total_pages": len(all_processed_data),
            # "total_chunks": len(all_chunks),
            "results": {
                "processed_data": all_processed_data,
                # "chunks": all_chunks
            },
            "skipped_documents": skipped_files
        }

        return JSONResponse(content=response_data)

    except Exception as e:
        logger.error(f"Error processing documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if processing_dir:
            cleanup_directory(processing_dir)

@app.get("/get-file")
async def get_file(file_path: str = Query(...)):
    """
    Get local file as base64 or as public download link.
    """
    try:
        path = Path(file_path)

        # Ensure base directory is 'images'
        full_path = Path("images") / path.relative_to("images")

        if not full_path.exists() or not full_path.is_file():
            raise HTTPException(status_code=404, detail="File not found")

        with open(full_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
        return {
            "file_name": full_path.name,
            "base64": encoded,
            "path": str(full_path)
        }
    except Exception as e:
        logger.error(f"Error retrieving file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/delete-document")
async def delete_document(
    document_id: str
):
    """
    Delete a document from the database.
    """
    try:
        # Initialize ChromaDB client using config values
        client = chromadb.PersistentClient(path=settings["vectorstore_persist_directory"])
        collection = client.get_collection(name=settings["vectorstore_collection_name"])

        # Get initial count and document info
        initial_results = collection.get()
        initial_count = len(initial_results['ids'])

        logger.info("=" * 80)
        logger.info(f"Starting deletion process for document ID: {document_id}")
        logger.info(f"Initial total chunks in collection: {initial_count}")
        logger.info("=" * 80)

        # Get all chunks for the specified document ID
        results = collection.get(
            where={"document_id": document_id}
        )
        chunks_to_delete = results['ids']

        if not chunks_to_delete:
            logger.warning(f"No chunks found for document ID: {document_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Document with ID {document_id} not found"
            )

        # Delete the chunks
        collection.delete(
            where={"document_id": document_id}
        )

        # Get final count
        final_results = collection.get()
        final_count = len(final_results['ids'])

        # Log results
        logger.info("=" * 80)
        logger.info("Deletion Summary:")
        logger.info(f"Document ID processed: {document_id}")
        logger.info(f"Chunks deleted: {len(chunks_to_delete)}")
        logger.info(f"Initial chunk count: {initial_count}")
        logger.info(f"Final chunk count: {final_count}")
        logger.info("=" * 80)

        return {
            "status": "success",
            "message": "Document deleted successfully",
            "details": {
                "document_id": document_id,
                "chunks_deleted": len(chunks_to_delete),
                "initial_count": initial_count,
                "final_count": final_count
            }
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error occurred during deletion attempt: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error attempting to delete document: {str(e)}"
        )

@app.post("/modify-document")
async def modify_document(
    document_id: str
):
    """
    Modify a document's active status from "1" to "0" in the database.
    """
    try:
        logger.info(f"Attempting to modify document with ID: {document_id}")
        # Initialize ChromaDB client using config values
        client = chromadb.PersistentClient(path=settings["vectorstore_persist_directory"])
        collection = client.get_collection(name=settings["vectorstore_collection_name"])

        # Get initial count and document info
        initial_results = collection.get()
        initial_count = len(initial_results['ids'])

        logger.info("=" * 80)
        logger.info(f"Starting modification process for document ID: {document_id}")
        logger.info(f"Initial total chunks in collection: {initial_count}")
        logger.info("=" * 80)

        # Get all chunks for the specified document ID
        results = collection.get(
            where={"document_id": document_id}
        )
        chunks_to_modify = results['ids']

        if not chunks_to_modify:
            logger.warning(f"No chunks found for document ID: {document_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Document with ID {document_id} not found"
            )

        # Get current metadata for all chunks
        current_metadata = results['metadatas']

        # Update metadata to set active="0"
        updated_metadata = []
        for metadata in current_metadata:
            metadata['active'] = "0"
            updated_metadata.append(metadata)

        # Update the chunks with new metadata
        collection.update(
            ids=chunks_to_modify,
            metadatas=updated_metadata
        )

        # Get final count
        final_results = collection.get()
        final_count = len(final_results['ids'])

        # Log results
        logger.info("=" * 80)
        logger.info("Modification Summary:")
        logger.info(f"Document ID processed: {document_id}")
        logger.info(f"Chunks modified: {len(chunks_to_modify)}")
        logger.info(f"Initial chunk count: {initial_count}")
        logger.info(f"Final chunk count: {final_count}")
        logger.info("=" * 80)

        return {
            "status": "success",
            "message": "Document modified successfully",
            "details": {
                "document_id": document_id,
                "chunks_modified": len(chunks_to_modify),
                "initial_count": initial_count,
                "final_count": final_count
            }
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error occurred during modification attempt: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error attempting to modify document: {str(e)}"
        )

