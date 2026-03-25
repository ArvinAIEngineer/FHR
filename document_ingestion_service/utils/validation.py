import os
import logging
from typing import List

logger = logging.getLogger(__name__)

def validate_file_type(filename: str, allowed_types: List[str]) -> bool:
    """Check if a file's extension is in the allowed types."""
    try:
        file_ext = os.path.splitext(filename)[1].lower()
        return file_ext in allowed_types
    except Exception as e:
        logger.error(f"Error validating file type for {filename}: {str(e)}")
        return False
