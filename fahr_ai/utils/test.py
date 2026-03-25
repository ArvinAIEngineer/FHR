import json
import ast

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

# Example usage with your data
def test_extraction():
    # Your example content
    content = '''[["73\\nannual leave balance, if any; otherwise it shall be considered \\nunpaid leave.\\nThis leave may not be extended for similar terms.\\n2. Upon return of the employee, he shall submit to his entity a report \\nissued by the medical facility where the patient receives treatment, \\nincluding the name of the patient, the date of his admission to the \\nhospital, the person accompanying him and the date of discharge if he \\nhas completed the treatment; and any information requested by his \\nentity. If the employee does not submit this report, the direct superior \\nshall recommend to the Human Resources Department taking the \\nnecessary action against the employee.\\n3. A patient accompanying leave inside UAE shall not be granted in the \\nfollowing cases:\\nA. If the employee works on a temporary contract, part-time contract, \\nor works remotely.\\nB. The employee who is still on a probation period.\\nC. An employee who is undergoing treatment for poor performance.", {"source": "docs/اللائحة-التنفيذية-لقانون-الموارد-البشرية-باللغة-الإنجليزية EN.pdf", "page_number": 73, "trapped": "/False", "producer": "Adobe PDF Library 17.0", "total_pages": 124, "documentId": "4097d9ae-8bf1-4253-bd68-f435aab5d489", "page": 72, "page_image": "images/4097d9ae-8bf1-4253-bd68-f435aab5d489_page_73.png", "processed_at_str": "2025-06-22T09:18:51.885434", "documentName": "اللائحة-التنفيذية-لقانون-الموارد-البشرية-باللغة-الإنجليزية EN.pdf", "file_name": "اللائحة-التنفيذية-لقانون-الموارد-البشرية-باللغة-الإنجليزية EN.pdf", "pageNumber": 73, "moddate": "2025-05-08T08:15:44+04:00", "creationdate": "2025-05-08T08:15:38+04:00", "document_name": "اللائحة-التنفيذية-لقانون-الموارد-البشرية-باللغة-الإنجليزية EN.pdf", "creator": "Adobe InDesign 20.0 (Macintosh)", "document_id": "4097d9ae-8bf1-4253-bd68-f435aab5d489", "processed_at": "2025-06-22T09:18:51.885434", "page_label": "73"}]]'''
    
    # Extract reference data
    citations = extract_reference_data(content)
    
    # Print results
    print("Extracted Citations:")
    for i, citation in enumerate(citations, 1):
        print(f"{i}. {citation}")
    
    return citations

if __name__ == "__main__":
    test_extraction()