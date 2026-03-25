import os
import hashlib
import base64
from datetime import datetime
from typing import List, Dict, Any, Literal
from pathlib import Path
import subprocess

# Import extractors, loaders, vector store, summarizers from new structure
from modules.extractors.text_extractor import TextExtractor
from modules.extractors.image_extractor import ImageExtractor
from modules.extractors.table_extractor import TableExtractor
from modules.vectorstores.vectorstore_factory import VectorStoreManager
from core.config import settings

# Advanced modules
from modules.extractors.image_summarization.image_summarization import PageImageSummarizer
from modules.extractors.table_context_summarization.table_summarization import SummarizeTable
from modules.extractors.table_context_summarization.table_extraction import ExtractTable
from modules.extractors.topics_and_subtopics.topic_modelling_pipeline import TopicModelling

from langchain_openai import AzureChatOpenAI
from langchain_ollama import ChatOllama
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.messages import HumanMessage
import json
import pdfplumber
import platform
from docx2pdf import convert

from utils.logger import get_logger
from utils.file_ops import cleanup_directory, get_pdf_path_from_docx

logger = get_logger(__name__)

# Detect the OS
current_os = platform.system()


class IngestionPipeline:
    """
    A class to process PDF documents, extract content, and create chunks for vector storage.
    Migrated and refactored from DocumentProcessor.
    """

    def __init__(self):
        """Initialize the ingestion pipeline with all necessary components."""
        if settings["use_ollama"]:
            self.llm = ChatOllama(
                model=settings["ollama_llm_model"],
                base_url=settings["ollama_base_url"]
            )
        else:
            self.llm = AzureChatOpenAI(
                model_name=settings["llm_model"],
                temperature=settings["llm_temperature"],
                max_tokens=settings["llm_max_tokens"],
            )
        self.text_extractor = TextExtractor()
        self.table_extractor = TableExtractor()
        self.image_extractor = ImageExtractor()
        self.table_summarizer = SummarizeTable(
            model_name=settings["ollama_llm_model"] if settings["use_ollama"] else settings["llm_model"],
            model_url=settings["ollama_base_url"] + '/api/generate' if settings["use_ollama"] else settings[
                                                                                                       "llm_model"] + '/api/generate'
        )

        self.page_image_summarizer = PageImageSummarizer(self.llm)

        self.topic_subtopic = TopicModelling(
            model_name=settings["ollama_llm_model"] if settings["use_ollama"] else settings["llm_model"],
            model_url=settings["ollama_base_url"] + '/api/generate' if settings["use_ollama"] else settings[
                                                                                                       "llm_model"] + '/api/generate'
        )
        self.vector_store = VectorStoreManager()
        self.extract_table = ExtractTable()

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings["chunk_size"],
            chunk_overlap=settings["chunk_overlap"],
            length_function=len,
        )

    def _generate_document_id(self, content: str) -> str:
        """Generate a unique hash for the document."""
        return hashlib.sha256(content.encode()).hexdigest()

    def _detect_language(self, text: str) -> str:
        """Detect the language of the text using LLM."""
        try:
            prompt = (
                "Detect the language of this text and return only the ISO 639-1 language code.\n"
                "Respond with two-letter codes only, not three.\n"
                "Example: en or ar.\n\n"
                """You are a language detection assistant. Your task is to detect whether the given text is written in English or Arabic only.
                Return the result using the ISO 639-1 two-letter language code.

                Important Instructions:
                Only detect English (en) or Arabic (ar).
                Do not return any other language code or language name.
                Do not return "unknown", "und", or "can't detect" under any circumstances.
                Be strict: even if the text is short, noisy, or ambiguous, always return either en or ar based on the best possible guess.
                Output must be only the two-letter code on a single line — no explanation or formatting.

                Examples:
                Input: "Hello, how are you?" → Output: en
                Input: "مرحبا كيف حالك" → Output: ar
                Input: "The quick brown fox jumps over the lazy dog" → Output: en
                Input: "الكلب البني السريع يقفز فوق الثعلب الكسول" → Output: ar
                Input: "Meeting at 2 PM tomorrow" → Output: en
                Input: "اجتماع غداً الساعة ٢ مساءً" → Output: ar
                Input: "Please review the document" → Output: en
                Input: "يرجى مراجعة المستند" → Output: ar
                Input: "Hello مرحبا" → Output: en
                Input: "مرحبا Hello" → Output: ar"""
                f"Text:\n{text[:500]}"
            )
            
            response = self.llm.invoke([HumanMessage(content=prompt)])
            if hasattr(response, "content"):
                lang = response.content.strip().lower()
            else:
                lang = str(response).strip().lower()
            if lang == "ar":
                return "ar"
            return "en"
        except Exception as e:
            logger.error(f"Error detecting language: {str(e)}")
            # Default to English if there's an error, as per requirement to never return unknown
            return "en"

    def _determine_document_type(self, text: str) -> str:
        """Determine the document type (legal or HR) using LLM."""
        try:

            prompt = (
                f"Analyze the following text and determine if its content is primarily related to 'legal' matters "
                f"or'HR' (Human Resources) matter"
                f"Respond with only one word: 'legal' or 'hr'.\n\nText: {text[:1000]}"
            )
            answer = self.llm.invoke([HumanMessage(content=prompt)])

            doc_type_response = answer.content.strip().lower() if hasattr(answer, "content") else str(
                answer).strip().lower()

            if doc_type_response in ["legal", "hr"]:
                return doc_type_response
            else:
                logger.warning(
                    f"Unexpected document type response from LLM: '{doc_type_response}'. Defaulting to 'general'.")
                return "hr"  # defaulting to hr
        except Exception as e:
            logger.error(f"Error determining document type: {str(e)}")
            return "general"

    def process_document(self, file_path: str) -> Dict[str, Any]:
        """
        Process a document and create chunks.
        """
        try:
            # Create subfolder for page screenshots
            if file_path.endswith(".docx") or file_path.endswith(".doc"):
                # Use the new encapsulated function to get the PDF path
                temp_file_path = get_pdf_path_from_docx(file_path)
                logger.info(f"Converted {file_path} to PDF at {temp_file_path}.")
            else:
                temp_file_path = file_path
            file_path = Path(file_path)
            temp_file_path = Path(temp_file_path)
            processed_data = []
            chunks = []

            # Extract text based on file type
            extracted_text = self.text_extractor.extract_text(temp_file_path)
            document_id = self._generate_document_id(str(extracted_text))

            if self.vector_store.document_exists(document_id):
                logger.info(f"Document already exists in vector store: {document_id}")
                return {
                    "message": "Document already processed",
                    "document_id": document_id,
                    "document_name": temp_file_path.name
                }

            result = self.image_extractor.process_file(temp_file_path, f"images/{document_id}/")
            extract_images = result['embedded_images']
            extract_screenshots = result['page_screenshots']

            extract_tables = self.table_extractor.get_table_list(str(temp_file_path))

            # Determine document type based on the first page's content
            first_page_key = next(iter(extracted_text), None)
            doc_type = "general"
            if first_page_key and extracted_text[first_page_key]:
                doc_type = self._determine_document_type(extracted_text[first_page_key])
                logger.info(f"Document type {doc_type} detected")
            else:
                all_text_for_doc_type = " ".join(extracted_text.values())[:1000]
                if all_text_for_doc_type.strip():
                    doc_type = self._determine_document_type(all_text_for_doc_type)
                    logger.info(f"Document type {doc_type} detected")
                else:
                    logger.warning(
                        f"No text found in document {temp_file_path.name} to determine document type. Defaulting to 'general'.")

            for page_number in extracted_text.keys():
                logger.info(f"Processing page {int(page_number)} of {temp_file_path.name}")
                page_image = next(
                    (item["image_path"] for item in extract_screenshots if item["page_number"] == page_number), None)
                images_for_page = [img for img in extract_images if img["page_number"] == page_number]
                tables_for_page = [table for table in extract_tables if table['page'] == page_number]

                # Detect language
                language = self._detect_language(extracted_text[page_number])
                logger.info(f"language: {language}")

                # Generate table summaries
                if len(tables_for_page) > 0:
                    table_summaries = self.table_summarizer.get_summary(tables=tables_for_page)
                    joined_table_summary_text = "\n\n".join(
                        entry["detailed_summary"] for entry in table_summaries if "detailed_summary" in entry
                    )
                else:
                    joined_table_summary_text = None

                # Generate page image summary
                # page_image_summary = self.page_image_summarizer.get_page_image_summary(page_image)
                # page_ocr_text = page_image_summary.get("text", "")
                # image_summary_text = page_image_summary.get("summary", "")
                page_ocr_text, image_summary_text = "", ""

                # Combine text, table summaries, and image summary
                combined_text = page_ocr_text + extracted_text[page_number]
                if joined_table_summary_text:
                    combined_text += "\n\n" + joined_table_summary_text
                if image_summary_text:
                    combined_text += "\n\n" + image_summary_text

                # Topic and subtopic classification
                topic_subtopic = self.topic_subtopic.get_single_topic_and_subtopic(text=combined_text)

                base_metadata = {
                    "uuid": str(document_id) + str(page_number),
                    "document_name": file_path.name,
                    "document_type": doc_type,
                    "page_number": page_number,
                    "document_id": document_id,
                    "language": language,
                    "processed_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat(),
                    "version": "1.0",
                    "page_image": page_image,
                    # "page_image_summary": image_summary_text,
                    "page_tables": tables_for_page,
                    "extracted_images": images_for_page,
                    "topic": topic_subtopic.get('topic', 'Unknown'),
                    "subtopic": topic_subtopic.get('subtopic', 'Unknown')
                }

                chunks.append({
                    "text": combined_text,
                    "metadata": {**base_metadata}
                })

            similarity_report = []
            if chunks:
                try:
                    inserted_uuids = self.vector_store.store_documents(chunks)
                    logger.info(f"Successfully inserted {len(inserted_uuids)} chunks for document {document_id}.")
                except Exception as store_err:
                    logger.error(f"Failed to store chunks for document {document_id}: {store_err}")
                    inserted_uuids = []

                # Perform similarity check for each newly inserted chunk
                if inserted_uuids:
                    logger.info(f"Performing similarity check for {len(inserted_uuids)} inserted chunks...")
                    for i, new_chunk_uuid in enumerate(inserted_uuids):
                        try:

                            similar_found = self.vector_store.find_similar_chunks_by_uuid(
                                query_uuid=new_chunk_uuid,
                                query_document_id=document_id,
                            )

                            for similar_chunk_data in similar_found:
                                similarity_report.append({
                                    "newly_inserted_document_id": document_id,
                                    "newly_inserted_chunk_uuid": new_chunk_uuid,
                                    "similar_document_id": similar_chunk_data.get("similar_document_id"),
                                    "similar_chunk_chroma_id": similar_chunk_data.get("similar_chunk_chroma_id"),
                                    "similarity_score": similar_chunk_data.get("similarity_score")
                                })
                        except Exception as sim_err:
                            logger.error(f"Error during similarity check for chunk {new_chunk_uuid}: {sim_err}")

            if similarity_report:
                report_filename = f"similarity_report_{file_path.stem}_{document_id}.json"
                try:
                    with open(report_filename, "w", encoding="utf-8") as f_report:
                        json.dump(similarity_report, f_report, ensure_ascii=False, indent=2)
                    logger.info(f"Similarity report saved to: {report_filename}")
                except Exception as report_err:
                    logger.error(f"Failed to save similarity report to {report_filename}: {report_err}")


            processed_data.append(chunks)
            debug_output = {
                "processed_data": processed_data,
            }
            ## Use below code block for separate debug output per file ingested
            debug_file_path = f"debug_output_{file_path.stem}.json"
            try:
                with open(debug_file_path, "w", encoding="utf-8") as f:
                    json.dump(debug_output, f, ensure_ascii=False, indent=2)
                logger.info(f"Debug JSON written to: {debug_file_path}")
            except Exception as debug_err:
                logger.warning(f"Failed to write debug JSON: {debug_err}")
            return {
                "processed_data": processed_data,
            }

        except Exception as e:
            logger.error(f"Error processing document {file_path}: {str(e)}")
            raise