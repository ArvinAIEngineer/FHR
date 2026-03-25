import fitz  # PyMuPDF
import pandas as pd
from typing import List, Dict
import camelot
from utils.logger import get_logger
from utils.file_ops import cleanup_directory, get_pdf_path_from_docx

logger = get_logger(__name__)

class TableExtractor:
    def __init__(self):
        self.logger = logger
        pass

    def extract_tables(self, pdf_path: str, pages: str = 'all') -> List[pd.DataFrame]:
        """
        Extract tables from a PDF file using camelot-py.

        Args:
            pdf_path (str): Path to the PDF file
            pages (str): Pages to extract tables from (default: 'all')

        Returns:
            List[pd.DataFrame]: List of extracted tables as pandas DataFrames
        """
        tables = camelot.read_pdf(str(pdf_path), pages=pages)
        return [table.df for table in tables]

    def extract_tables_with_metadata(self, pdf_path: str, pages: str = 'all') -> List[Dict]:
        """
        Extract tables from a PDF file with additional metadata.

        Args:
            pdf_path (str): Path to the PDF file
            pages (str): Pages to extract tables from (default: 'all')

        Returns:
            List[Dict]: List of dictionaries containing tables and their metadata
        """
        tables = camelot.read_pdf(str(pdf_path), pages=pages)
        result = []

        for table in tables:
            result.append({
                'page': table.page,
                'order': table.order,
                'accuracy': table.accuracy,
                'whitespace': table.whitespace,
                'data': table.df.to_dict('records')
            })

        return result

    def get_table_list(self, path: str) -> list:
        """
        Extract tables as CSV and parsing report for each table.

        Args:
            path (str): Path to the PDF file

        Returns:
            list: List of dicts with CSV and parsing report for each table
        """
        self.logger.info(f"Extracting tables from {path}")
        try:
            tables = camelot.read_pdf(str(path), pages="all", flavor="stream", split_text=True)
        except Exception as e:
            self.logger.error(f"Error reading PDF with Camelot: {e}")
            return []

        self.logger.info(f"Found {len(tables)} tables in {path}")

        if not tables or len(tables) == 0:
            self.logger.warning(f"No tables found in PDF: {path}")
            return []

        organized = []
        for i, table in enumerate(tables):
            try:
                csv_str = table.df.to_csv(index=False)
                report = table.parsing_report
                organized.append({"table_csv": csv_str, **report})
            except Exception as e:
                self.logger.error(f"Error processing table {i} in {path}: {e}")
                continue

        return organized
