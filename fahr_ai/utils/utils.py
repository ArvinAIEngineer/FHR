import sys
sys.path.append("./")
from typing import Optional, Dict, Any, List
import re
from utils.logger import get_logger
import logging
import json
from langchain_core.messages import ToolMessage, HumanMessage, AIMessage, SystemMessage
import ast

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

def extract_reference_data(tool_message_content):
    """
    Extract reference data from tool message content and format it as citations.
    
    Args:
        tool_message_content (str): The content string from the tool message
        
    Returns:
        list: List of citation dictionaries with documentId, documentName, pageNumber, screenshotUrl
    """
    citations = []
    
    try:
        # Parse the content string as a Python literal (list of tuples)
        parsed_content = ast.literal_eval(tool_message_content)
        
        # Check if it's a list (the main structure)
        if isinstance(parsed_content, list):
            for item in parsed_content:
                # Each item should be a tuple with (text_content, metadata_dict)
                if isinstance(item, (list, tuple)) and len(item) >= 2:
                    text_content = item[0]  # First element is the text
                    metadata = item[1]      # Second element is the metadata dict
                    
                    # Process metadata if it's a dictionary
                    if isinstance(metadata, dict):
                        citation = {
                            "documentId": metadata.get("documentId", "") or metadata.get("document_id", ""),
                            "documentName": metadata.get("documentName", "") or metadata.get("document_name", ""),
                            "pageNumber": str(metadata.get("pageNumber", metadata.get("page_number", 1))),
                            "screenshotUrl": metadata.get("page_image", "")
                        }
                        
                        # Only add if we have meaningful data
                        if citation["documentId"] or citation["documentName"]:
                            citations.append(citation)
    
    except (ValueError, SyntaxError) as e:
        print(f"Error parsing tool message content: {e}")
        
        # Fallback: try to parse as JSON if literal_eval fails
        try:
            parsed_content = json.loads(tool_message_content)
            if isinstance(parsed_content, list):
                for item in parsed_content:
                    if isinstance(item, (list, tuple)) and len(item) >= 2:
                        metadata = item[1]
                        if isinstance(metadata, dict):
                            citation = {
                                "documentId": metadata.get("documentId", "") or metadata.get("document_id", ""),
                                "documentName": metadata.get("documentName", "") or metadata.get("document_name", ""),
                                "pageNumber": str(metadata.get("pageNumber", metadata.get("page_number", 1))),
                                "screenshotUrl": metadata.get("page_image", "")
                            }
                            
                            if citation["documentId"] or citation["documentName"]:
                                citations.append(citation)
        except json.JSONDecodeError:
            print("Failed to parse content as JSON as well")
    
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

def reduce_personal_info(full_data: dict) -> dict:
    """
    Reduces the full personal data dictionary to only include selected fields inside 'personalInfo'.
    
    :param full_data: Original dictionary with all personal data fields.
    :param fields_to_keep: List of keys to retain in the reduced output.
    :return: A new dictionary with the reduced personal info.
    """
    fields_to_keep = [
        "bayanatiMobileNumber", "emailAddress", "emiratesId", "educationLevel", "perInformation13",
        "religion", "assignmentId", "homeNumber", "nationality", "location", "managerNumber",
        "organization", "birthCity", "officeNumber", "maritalStatus",
        "placeOfBirthEn", "workNumber", "job", "motherNameAr", "emiratesIdExpirtyDate",
        "nationalIdentifier", "personId", "grade", "entityCode", "experience",
        "employeE_TITLE_ID", "joinDate", "employeeTitle", "employeeNumber", "gender",
        "mobileNum", "dateOfBirth", "countryOfBirth", "age", "emergencyContact",
        "payrollId", "previousNationality", "employeeName", "managerName"
    ]
    reduced_data = {
        key: full_data.get(key) for key in fields_to_keep if key in full_data}
    return reduced_data

def extract_tool_outputs_from_events(events: list) -> list[dict]:
    """
    Extract structured JSON tool outputs (content + name) from LangGraph streamed events.
    
    Returns a list of dicts: [{"name": tool_name, "content": parsed_json}, ...]
    """
    api_widgets = []

    for event in events:
        for value in event.values():
            if isinstance(value, list):
                for msg in value:
                    if isinstance(msg, ToolMessage) and msg.name!="get_knowledge_documents":
                        try:
                            api_widgets.append({
                                "widgetType": msg.name.upper(),
                                "data": msg.content
                            })
                        except json.JSONDecodeError:
                            continue
    unique_widgets = list({json.dumps(w, sort_keys=True) for w in api_widgets})
    unique_widgets = [json.loads(w) for w in unique_widgets]

    return unique_widgets

def filter_think(message:AIMessage):
    # Remove entire <think>\n...\n</think>\n block using DOTALL to match across lines
    cleaned = re.sub(r"<think>\n.*?\n</think>\n", "", message.content, flags=re.DOTALL).strip()
    # Optional cleanup of excessive whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if cleaned not in ["", "\n"]:
        return AIMessage(content=cleaned)
    else:
        return None
