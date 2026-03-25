import sys
sys.path.append('./')
import os
import json
import base64
import requests
import logging
import base64
import io
from typing import Union, Dict, Any, Optional
from PIL import Image
from langchain.schema import HumanMessage
from langchain.chat_models.base import BaseChatModel
import json
from utils.logger import get_logger # Import get_logger utility
from core.config import settings


# Constants for configuration
CURRENT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
from core.config import settings

# class PageImageSummarizer:
#     """
#     A class to perform page image summarization using a language model.
#     """

#     def __init__(self, model_name: str, model_url: str):
#         """
#         Initializes the PageImageSummarizer class with model details.

#         Args:
#             model_name (str): Name of the model.
#             model_url (str): URL of the model's API endpoint.
#         """
#         self.model_name = model_name
#         self.model_url = model_url
#         self.headers = {"Content-Type": "application/json", "Accept": "application/json"}
#         self.page_image_prompt_en = self.get_prompt(settings["page_image_prompt_en_path"])
#         self.page_image_prompt_ar = self.get_prompt(settings["page_image_prompt_ar_path"])

#     def get_prompt(self, path: str) -> str:
#         """
#         Reads and returns the content of a prompt file.

#         Args:
#             path (str): Relative path to the prompt file.

#         Returns:
#             str: Content of the prompt file.
#         """
#         path = os.path.join(CURRENT_DIRECTORY, path)
#         with open(path, "r", encoding='utf-8') as f:
#             prompt = f.read()
#         return prompt

#     def query_llm(self, payload: dict, url: str) -> str:
#         """
#         Sends a POST request to the language model API and retrieves the response.

#         Args:
#             payload (dict): Payload to send to the API.
#             url (str): API endpoint URL.

#         Returns:
#             str: Response from the API.
#         """
#         response = requests.post(url=url, headers=self.headers, json=payload)
#         return response.json()["response"]

#     def get_page_image_summary(self, page_image: str, language: str = "en") -> dict:
#         """
#         Generates a summary for a page image (full page screenshot).

#         Args:
#             page_image (str): Path to the page image file.
#             language (str): Language for the summary ('en' or 'ar').

#         Returns:
#             dict: A dictionary containing:
#                 - Page image path
#                 - Summary in the specified language
#                 - Language code
#         """
#         try:
#             # Select prompt based on language
#             prompt = self.page_image_prompt_ar if language == "ar" else self.page_image_prompt_en

#             # Read and encode the image
#             with open(page_image, "rb") as image_file:
#                 encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

#             # Prepare payload
#             payload = {
#                 "prompt": prompt,
#                 "model": self.model_name,
#                 "images": [encoded_image],
#                 "stream": False,
#             }

#             # Get summary from LLM
#             response = self.query_llm(payload, self.model_url)

#             return {
#                 "page_image": page_image,
#                 "image_summary": response,
#                 "language": language
#             }

#         except Exception as e:
#             logger.error(f"Error generating page image summary: {str(e)}")
#             return {
#                 "page_image": page_image,
#                 "image_summary": "",
#                 "language": language,
#                 "error": str(e)
#             }

class PageImageSummarizer:
    def __init__(self,
                 llm_model: Optional[BaseChatModel] = None):
        """
        Initialize Gemma OCR with LangChain ChatOpenAI interface

        Args:
            api_key: API key for the service (can be dummy for local Ollama)
            base_url: Base URL for the API endpoint
            model_name: Name of the Gemma model to use
        """
        self.llm = llm_model
        self.logger = get_logger(__name__)

    def encode_image_to_base64(self, image_input: Union[str, bytes, Image.Image]) -> str:
        """
        Convert image to base64 string

        Args:
            image_input: Image file path, bytes, or PIL Image object

        Returns:
            Base64 encoded string of the image
        """
        try:
            if isinstance(image_input, str):
                # If it's a file path
                with open(image_input, "rb") as image_file:
                    return base64.b64encode(image_file.read()).decode('utf-8')

            elif isinstance(image_input, bytes):
                # If it's already bytes
                return base64.b64encode(image_input).decode('utf-8')

            elif isinstance(image_input, Image.Image):
                # If it's a PIL Image
                buffer = io.BytesIO()
                image_input.save(buffer, format='PNG')
                return base64.b64encode(buffer.getvalue()).decode('utf-8')

            else:
                raise ValueError("Unsupported image input type")

        except Exception as e:
            self.logger.error(f"Error encoding image: {str(e)}")
            raise

    def create_ocr_prompt(self, language_hint: Optional[str] = None) -> str:
        """
        Create a comprehensive OCR prompt with language detection

        Args:
            language_hint: Optional hint about expected language

        Returns:
            Formatted prompt string
        """
        base_prompt = """You are an advanced OCR (Optical Character Recognition) system. Your task is to:

1. Analyze the image and detect the language(s) present
2. Extract ALL text content accurately, preserving formatting where possible
3. Handle multiple languages (especially Arabic and English)
4. Maintain text structure (paragraphs, lists, tables if present)

Please provide your response in the following JSON format:
{
    "detected_languages": ["language1", "language2"],
    "primary_language": "main_language",
    "text_direction": "ltr/rtl",
    "extracted_text": "complete extracted text here",
    "summary": "summary of the extracted text here in same primary language",
    "confidence": "high/medium/low",
    "text_regions": [
        {
            "text": "text in this region",
            "language": "detected language",
            "position": "approximate position description"
        }
    ],
    "formatting_notes": "any special formatting observations"
}

Important guidelines:
- For Arabic text, ensure proper right-to-left reading direction
- Preserve line breaks and paragraph structure
- If text is unclear, indicate uncertainty in confidence level
- Handle mixed language content appropriately
- Extract text from tables, forms, or structured layouts carefully"""

        if language_hint:
            base_prompt += f"\n\nLanguage hint: The image likely contains {language_hint} text."

        return base_prompt

    def get_page_image_summary(self,
                    image_input: Union[str, bytes, Image.Image],
                    language_hint: Optional[str] = None,
                    custom_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform OCR on image using Gemma model

        Args:
            image_input: Image to process (file path, bytes, or PIL Image)
            language_hint: Optional hint about expected language
            custom_prompt: Optional custom prompt to override default

        Returns:
            Dictionary containing OCR results and metadata
        """
        try:
            # Encode image to base64
            base64_image = self.encode_image_to_base64(image_input)

            # Create prompt
            prompt = custom_prompt or self.create_ocr_prompt(language_hint)

            # Create message with image
            message = HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}",
                            "detail": "high"
                        }
                    }
                ]
            )

            # Get response from model
            self.logger.info("Sending image to Gemma model for OCR processing...")
            response = self.llm.invoke([message])

            # Parse response
            result = self.parse_response(response.content)

            return {
                "page_image": image_input,
                "text": result.get('extracted_text'),
                "summary": result.get('summary'),
                "language": result.get('primary_language')
            }

        except Exception as e:
            self.logger.error(f"OCR processing failed: {str(e)}")
            return {
                "processing_status": "error",
                "error_message": str(e),
                "text": "",
                "summary": "",
                "detected_languages": [],
                "confidence": "low"
            }

    def parse_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse the model's response and extract structured data

        Args:
            response_text: Raw response from the model

        Returns:
            Parsed dictionary with OCR results
        """
        try:
            # Try to parse as JSON first
            if response_text.strip().startswith('{'):
                return json.loads(response_text)

            # If not JSON, try to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())

            # Fallback: create structured response from plain text
            return {
                "detected_languages": ["unknown"],
                "primary_language": "unknown",
                "text_direction": "ltr",
                "extracted_text": response_text,
                "summary": "",
                "confidence": "medium",
                "text_regions": [
                    {
                        "text": response_text,
                        "language": "unknown",
                        "position": "full image"
                    }
                ],
                "formatting_notes": "Fallback parsing - JSON structure not detected"
            }

        except json.JSONDecodeError as e:
            self.logger.warning(f"Failed to parse JSON response: {str(e)}")
            return {
                "detected_languages": ["unknown"],
                "primary_language": "unknown",
                "text_direction": "ltr",
                "extracted_text": response_text,
                "summary": "",
                "confidence": "low",
                "text_regions": [],
                "formatting_notes": f"JSON parsing error: {str(e)}"
            }