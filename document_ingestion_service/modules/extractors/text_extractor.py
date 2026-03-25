import fitz  # PyMuPDF
from core.config import settings
import docx
import fitz  # PyMuPDF
import docx
from typing import List, Dict, Union, Optional

class TextExtractor:
    def __init__(self):
        pass

    def extract_text(self, file_path: str) -> Dict[int, str]:
        """
        Extract text from a PDF file.

        Args:
            pdf_path (str): Path to the PDF file

        Returns:
            Dict[int, str]: Dictionary with page numbers as keys and text content as values
        """
        doc = fitz.open(file_path)
        text_content = {}

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            text_content[page_num + 1] = text.strip()

        doc.close()
        return text_content
