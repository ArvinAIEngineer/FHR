import os
import camelot
from typing import List, Dict, Optional, Tuple


class ExtractTable:
    """
    A class to extract tables from PDF files, format them, and organize the extracted data.
    """

    def __init__(self, min_accuracy: float = 0.95, min_rows: int = 2, min_columns: int = 2):
        """
        Initializes the ExtractTable class with attributes for storing extracted tables,
        their string representations, and parsing reports.
        """
        self.min_accuracy = min_accuracy*100.0
        self.min_rows = min_rows
        self.min_columns = min_columns
        self.table_list = None  # List of extracted tables
        self.table_strings = None  # List of table data in CSV string format
        self.table_report = None  # List of parsing reports for the extracted tables

    def extract_tables(self, path: str):
        """
        Extracts tables from a PDF file using Camelot.

        Args:
            path (str): The file path to the PDF.

        Returns:
            table_list: A list of tables extracted from the PDF.
        """
        # Use Camelot to read tables from the PDF
        table_list = camelot.read_pdf(path, pages="all", flavor="stream", split_text=True)
        filted_table_list = self.filter_quality_tables(table_list)

        return filted_table_list

    def filter_quality_tables(self, tables: camelot.core.TableList) -> List[Tuple[int, camelot.core.Table]]:
        """
        Filters tables based on quality metrics and minimum requirements.

        Args:
            tables (camelot.core.TableList): List of extracted tables

        Returns:
            List[Tuple[int, camelot.core.Table]]: List of (index, table) tuples for quality tables
        """
        quality_tables = []

        for i, table in enumerate(tables):
            # Check parsing accuracy
            accuracy = table.parsing_report.get('accuracy', 0)

            # Check minimum rows
            row_count = len(table.df)
            col_count = len(table.df.columns)

            # Check if table has meaningful content (not all empty)
            has_content = not table.df.empty and table.df.notna().any().any()

            if (accuracy >= self.min_accuracy and
                    row_count >= self.min_rows and
                    col_count >= self.min_columns and
                    has_content):
                quality_tables.append((i, table))

        return quality_tables

    def organize_response(self, table_strings: list, table_reports: list) -> list:
        """
        Organizes the extracted table data and their parsing reports into a structured format.

        Args:
            table_strings (list): List of table data in CSV string format.
            table_reports (list): List of parsing reports for the extracted tables.

        Returns:
            list: A list of dictionaries containing table data and their corresponding reports.
        """
        organized_tables = []

        # Combine table data and parsing reports into a single structure
        for table_string, report in zip(table_strings, table_reports):
            organized_tables.append(
                {
                    "table_csv": table_string,
                    **report,  # Merge the parsing report into the dictionary
                }
            )
        return organized_tables

    def get_table_list(self, path: str) -> list:
        """
        Extracts tables from a PDF, formats them as CSV strings, and organizes the data.

        Args:
            path (str): The file path to the PDF.

        Returns:
            list: A list of dictionaries containing formatted table data and parsing reports.
        """
        # Extract tables from the PDF
        self.table_list = self.extract_tables(path)

        # Generate parsing reports for the extracted tables
        self.table_report = [table.parsing_report for table in self.table_list]

        # Convert table data to CSV string format
        self.table_strings = [table.df.to_csv(index=False) for table in self.table_list]

        # Organize the extracted data and reports
        organized_tables = self.organize_response(self.table_strings, self.table_report)

        return organized_tables
