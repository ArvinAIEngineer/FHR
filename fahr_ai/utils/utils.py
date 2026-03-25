import sys
sys.path.append("./")
from typing import Optional, Dict, Any, List
import re
from utils.logger import get_logger
import logging
logger = get_logger()
logger.setLevel(logging.INFO)


def clean_text(text: str) -> str:
    """
    Remove unwanted characters while preserving Arabic, English, digits, 
    common punctuation, @, %, and newlines.
    """
    # Remove characters that are NOT in our allowed set
    # This approach might be more reliable for edge cases
    allowed_pattern = r'[^\u0600-\u06FFa-zA-Z0-9\s.,،؟:؛\-–—()@%\n]'
    cleaned = re.sub(allowed_pattern, '', text)
    return cleaned.strip()

def _extract_citations(result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract citation information from the workflow result.

    Args:
        result: The result dictionary from the RAG workflow

    Returns:
        List of citation dictionaries with documentId, documentName, pageNumber, page_image
    """
    citations = []

    # Extract from reference_data if available
    reference_data = result.get("memory", {}).get("reference_data", [])

    for ref in reference_data:
        if isinstance(ref, dict):
            # Extract metadata from the document

            citation = {
                "documentId": ref.get("documentId", ""),
                "documentName": ref.get("documentName", ""),
                "pageNumber": str(ref.get("pageNumber", 1)),
                "screenshotUrl": ref.get("page_image", "")
            }

            # Only add if we have meaningful data
            if citation["documentId"] or citation["documentName"]:
                citations.append(citation)

    return citations

def detect_language(text: str) -> str:
    """
    Improved language detection with higher accuracy and fallback mechanisms.
    Returns 'ar' for Arabic, 'en' for English.
    """
    if not text or text.strip() == "":
        return "en"  # Default to English for empty text

    # Detect if text contains Arabic characters
    arabic_pattern = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]+')
    has_arabic = bool(arabic_pattern.search(text))

    # Detect if text contains English characters
    english_pattern = re.compile(r'[a-zA-Z]+')
    has_english = bool(english_pattern.search(text))

    # Log detection results for debugging
    logger.debug(f"Language detection: has_arabic={has_arabic}, has_english={has_english}")

    # Decision logic with fallbacks
    if has_arabic and not has_english:
        return "ar"
    elif has_english and not has_arabic:
        return "en"
    elif has_arabic and has_english:
        # Mixed language - count characters to determine dominant language
        arabic_chars = len(re.findall(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))

        logger.debug(f"Mixed language: arabic_chars={arabic_chars}, english_chars={english_chars}")
        return "ar" if arabic_chars > english_chars else "en"
    else:
        # No clear language indicators, fallback to English
        return "en"