import os
import shutil
import tempfile
import logging
from typing import List
from fastapi import UploadFile
from datetime import datetime
import platform
import subprocess
from docx2pdf import convert

logger = logging.getLogger(__name__)

def create_processing_directory() -> str:
    """Create a unique directory for processing files."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_dir = os.path.join(tempfile.gettempdir(), f"ingestion_processing_{timestamp}")
        os.makedirs(temp_dir, exist_ok=True)
        logger.info(f"Created processing directory: {temp_dir}")
        return temp_dir
    except Exception as e:
        logger.error(f"Error creating processing directory: {str(e)}")
        raise

def save_uploaded_files(files: List[UploadFile], directory: str) -> List[str]:
    """Save uploaded files to the specified directory."""
    saved_paths = []
    try:
        for file in files:
            file_path = os.path.join(directory, file.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            saved_paths.append(file_path)
            logger.info(f"Saved uploaded file: {file_path}")
        return saved_paths
    except Exception as e:
        logger.error(f"Error saving uploaded files: {str(e)}")
        raise

def cleanup_directory(directory: str) -> None:
    """Remove a directory and its contents if it exists."""
    try:
        if os.path.exists(directory):
            shutil.rmtree(directory)
            logger.info(f"Cleaned up directory: {directory}")
    except Exception as e:
        logger.error(f"Error cleaning up directory {directory}: {str(e)}")
        raise

def find_converted_pdf(docx_path):
    """
    Given a DOCX path, find the corresponding PDF in the same directory.
    Returns the PDF path if found, else raises FileNotFoundError.
    Works for both Linux and Windows, and handles non-ASCII filenames.
    """
    base_dir = os.path.dirname(docx_path)
    base_name = os.path.splitext(os.path.basename(docx_path))[0]
    expected_pdf = os.path.join(base_dir, f"{base_name}.pdf")
    if os.path.exists(expected_pdf):
        return expected_pdf
    # Fallback: search for any PDF in the directory created/modified after the DOCX
    docx_mtime = os.path.getmtime(docx_path)
    pdf_candidates = []
    for fname in os.listdir(base_dir):
        if fname.lower().endswith('.pdf'):
            fpath = os.path.join(base_dir, fname)
            # Only consider PDFs created/modified after the DOCX
            if os.path.getmtime(fpath) >= docx_mtime:
                pdf_candidates.append(fpath)
    if pdf_candidates:
        # Return the most recently modified PDF
        return max(pdf_candidates, key=os.path.getmtime)
    raise FileNotFoundError(f"No PDF found in {base_dir} after converting {docx_path}")

def get_pdf_path_from_docx(docx_path):
    """
    Convert DOCX to PDF and return the PDF path, handling both Linux and Windows.
    """
    current_os = platform.system()
    base_dir = os.path.dirname(docx_path)
    if current_os == "Linux":
        subprocess.run(['libreoffice', '--headless', '--convert-to', 'pdf', docx_path, '--outdir', base_dir],
                       check=True)
    elif current_os == "Windows":
        convert(docx_path)
    else:
        raise Exception(f"Unsupported OS: {current_os}")
    return find_converted_pdf(docx_path)
