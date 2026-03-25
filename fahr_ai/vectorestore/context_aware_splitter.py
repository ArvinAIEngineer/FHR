import re
import tiktoken
from typing import List, Dict, Optional, Tuple
from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate
from langchain.schema import Document
from langchain_community.document_loaders import PyPDFLoader
from dataclasses import dataclass
import logging
import os
os.environ['NO_PROXY'] = '10.254.115.17, 10.254.140.69'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ChunkConfig:
    """Configuration for document chunking"""
    max_tokens: int = 1000
    overlap_tokens: int = 50
    ollama_model: str = "gemma3:27b"
    ollama_base_url: str = "http://10.254.140.69:11434"
    use_llm_merging: bool = True 
    encoding_model: str = "cl100k_base"  # GPT-4 encoding

class LegalDocumentChunker:
    """
    A specialized document chunker for legal documents that:
    1. Splits by articles first, then paragraphs
    2. Uses LLM to determine if chunks should be merged based on context
    3. Respects token limits
    4. Handles both Arabic and English text
    """
    
    def __init__(self, config: ChunkConfig):
        self.config = config

        if config.use_llm_merging:
            self.llm = OllamaLLM(
                model=config.ollama_model,
                base_url=config.ollama_base_url,
            )
        
        # Initialize tokenizer
        try:
            self.tokenizer = tiktoken.get_encoding(config.encoding_model)
        except Exception as e:
            logger.warning(f"Could not load tiktoken encoder: {e}. Using approximate token counting.")
            self.tokenizer = None
        
        # Regex patterns for article detection (Arabic and English)
        self.article_patterns = [
            # English: Article (1), Article (3):, Art. II, SECTION V
            r'(?i)^\s*(article|art\.?|section|sec\.?)\s*\(?\s*(\d+|[ivxlcdm]+|one|two|three|four|five|six|seven|eight|nine|ten)\s*\)?\s*[:.\-]?',  

            # English alternate: 5. Article or II) Section
            r'(?i)^\s*(\d+|[ivxlcdm]+|one|two|three|four|five|six|seven|eight|nine|ten)\s*[\.\)]\s+(article|art\.?|section|sec\.?)',  

            # Arabic: المادة )4( — RTL style
            r'^\s*(المادة|مادة)\s*[\)\(]\s*(\d+|[٠-٩]+|[١-٩]+)\s*[\)\(]\s*[:.\-]?',  

            # Arabic: المادة (4) — LTR style
            r'^\s*(المادة|مادة)\s*\(\s*(\d+|[٠-٩]+|[١-٩]+)\s*\)\s*[:.\-]?', 
            r'^\s*(المادة|مادة)\s*[\)\(]?\s*(\d+|[٠-٩]+|[١-٩]+)\s*[\)\(]?\s*[:.\-]?', 

            # Arabic: مادة 4. or المادة 5:
            r'^\s*(المادة|مادة)\s+(\d+|[٠-٩]+|[١-٩]+)\s*[:.\-]?',  

            # Arabic: الفقرة (2), البند )3(
            r'^\s*(الفقرة|البند)\s*[\)\(]?\s*(\d+|[٠-٩]+|[١-٩]+)\s*[\)\(]?\s*[:.\-]?',  

            # Arabic reverse: ٣. مادة
            r'^\s*(\d+|[٠-٩]+|[١-٩]+)\s*[\.\)]\s+(مادة|المادة|بند|الفقرة)', 
                # Pattern 1: )5المادة or ) 4المادة — closing paren before Arabic word + number
            r'\)\s*(\d+|[٠-٩]+)\s*(المادة|مادة)',

            # Pattern 2: )5 المادة or )٤ مادة — add optional space between number and word
            r'\)\s*(\d+|[٠-٩]+)\s+(المادة|مادة)',

            # Pattern 3: المادة )5( — alternate format with parens around the number
            r'(المادة|مادة)\s*\(\s*(\d+|[٠-٩]+)\s*\)'
        ]
        # Create the contextual merging prompt
        self.merge_prompt = PromptTemplate(
            input_variables=["chunk1", "chunk2"],
            template="""
You are given two consecutive chunks from a document. Your task is to decide whether they should be merged into a single chunk for better clarity and coherence.

CHUNK 1:
{chunk1}

CHUNK 2:
{chunk2}

Carefully consider the following:

Can chunk 2 be clearly understood on its own, without relying heavily on chunk 1?
Is chunk 2 a direct continuation or conclusion of an incomplete idea from chunk 1?
Would separating the chunks result in loss of critical meaning, context, or coherence?
Is chunk 2 too ambiguous or vague when read alone?
Are the two chunks tightly connected semantically, such that separating them would disrupt understanding?

Important:
Only suggest merging if chunk 2 cannot stand on its own due to lack of clarity, completeness, or dependency on chunk 1.

Respond with only "MERGE" or "SEPARATE".

Decision:"""
        )
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken or approximation"""
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        else:
            # Approximate: 1 token ≈ 4 characters for mixed language text
            return len(text) // 4

    def detect_articles(self, text: str) -> List[Tuple[int, int, str]]:
        """
        Detect articles in the text and return their positions
        Returns: List of (start_pos, end_pos, article_title)
        - Keeps preamble if it exists before the first article
        - Prevents trimming content between articles
        """
        articles = []
        lines = text.split('\n')
        current_pos = 0
        article_positions = []
        first_article_found = False

        # Cache start positions and matched lines
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                current_pos += len(line) + 1
                continue

            for pattern in self.article_patterns:
                if re.match(pattern, stripped):
                    article_positions.append((current_pos, stripped))
                    if not first_article_found and current_pos > 0:
                        # Capture preamble
                        preamble_text = text[:current_pos].strip()
                        if preamble_text:
                            articles.append((0, current_pos, "Preamble"))
                        first_article_found = True
                    break

            current_pos += len(line) + 1

        # Add last article’s end as end of text
        article_positions.append((len(text), None))

        # Create article spans
        for i in range(len(article_positions) - 1):
            start_pos, title = article_positions[i]
            end_pos, _ = article_positions[i + 1]
            articles.append((start_pos, end_pos, title))

        return articles

    
    def split_by_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs, handling both Arabic and English"""
        # Split by double newlines first, then by single newlines if paragraphs are too long
        paragraphs = []
        
        # Initial split by double newlines
        sections = re.split(r'\n\s*\n+', text.strip())
        
        for section in sections:
            section = section.strip()
            if not section:
                continue
            
            # If section is too long, split by single newlines
            if self.count_tokens(section) > self.config.max_tokens:
                lines = section.split('\n')
                current_para = ""
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    test_para = current_para + '\n' + line if current_para else line
                    if self.count_tokens(test_para) <= self.config.max_tokens:
                        current_para = test_para
                    else:
                        if current_para:
                            paragraphs.append(current_para)
                        current_para = line
                
                if current_para:
                    paragraphs.append(current_para)
            else:
                paragraphs.append(section)
        
        return paragraphs
    
    def should_merge_chunks(self, chunk1: str, chunk2: str) -> bool:
        """Use LLM to determine if two chunks should be merged"""
        if not self.config.use_llm_merging or not self.llm:
            logger.info("LLM merging disabled, not merging chunks")
            return False
        try:
            # Truncate chunks if they're too long for the LLM context
            max_chunk_length = 2000  # Adjust based on your model's context window
            
            if len(chunk1) > max_chunk_length:
                chunk1 = chunk1[:max_chunk_length] + "..."
            if len(chunk2) > max_chunk_length:
                chunk2 = chunk2[:max_chunk_length] + "..."
            
            prompt = self.merge_prompt.format(chunk1=chunk1, chunk2=chunk2)
            response = self.llm.invoke(prompt)
            response = re.sub(r"<think>\n.*?\n</think>\n", "", response, flags=re.DOTALL).strip()
            # Parse the response
            decision = response.strip().upper()
            should_merge = "MERGE" in decision
            
            logger.info(f"Merge decision: {decision}")
            return should_merge
            
        except Exception as e:
            logger.error(f"Error in LLM merge decision: {e}")
            # Default to not merging on error
            return False
    
    def merge_chunks_with_context(self, chunks: List[str]) -> List[str]:
        """Merge chunks based on contextual relationship using LLM"""
        if len(chunks) <= 1:
            return chunks
        
        merged_chunks = []
        current_chunk = chunks[0]
        
        for i in range(1, len(chunks)):
            next_chunk = chunks[i]
            
            # Check if merging would exceed token limit
            combined_tokens = self.count_tokens(current_chunk + '\n\n' + next_chunk)
            
            if combined_tokens <= self.config.max_tokens:
                # Only check for contextual merging if token limit allows
                if self.should_merge_chunks(current_chunk, next_chunk):
                    current_chunk = current_chunk + '\n\n' + next_chunk
                    logger.info(f"Merged chunk {i} with previous chunk")
                else:
                    merged_chunks.append(current_chunk)
                    current_chunk = next_chunk
            else:
                # Token limit exceeded, can't merge
                merged_chunks.append(current_chunk)
                current_chunk = next_chunk
        
        # Add the last chunk
        merged_chunks.append(current_chunk)
        
        return merged_chunks
    
    def chunk_document(self, document: Document) -> List[Document]:
        """
        Main method to chunk a legal document from a PyPDF Document object
        
        Args:
            document: A Document object from PyPDFLoader with page_content and metadata
            
        Returns:
            List[Document]: List of chunked Document objects
        """
        text = document.page_content
        original_metadata = document.metadata or {}
        
        if not text.strip():
            return []
        
        logger.info("Starting document chunking...")
        
        # Step 1: Try to detect articles
        articles = self.detect_articles(text)

        if articles:
            logger.info(f"Found {len(articles)} articles")
            chunks = []
            
            for start, end, title in articles:
                article_text = text[start:end].strip()
                
                # Extract topic from the article text (second line)
                topic = self.extract_topic_from_article(article_text)
                
                # If article is too long, split it further
                if self.count_tokens(article_text) > self.config.max_tokens:
                    logger.info(f"Article too long, splitting into paragraphs: {title}")
                    paragraphs = self.split_by_paragraphs(article_text)
                    # Add topic to each paragraph chunk
                    for paragraph in paragraphs:
                        chunks.append((paragraph, topic))
                else:
                    chunks.append((article_text, topic))
        else:
            logger.info("No articles found, splitting by paragraphs")
            paragraphs = self.split_by_paragraphs(text)
            # For non-article chunks, no topic metadata
            chunks = [(paragraph, None) for paragraph in paragraphs]

        # Step 2: Apply contextual merging (if enabled)
        if self.config.use_llm_merging:
            logger.info(f"Applying contextual merging to {len(chunks)} chunks")
            # Extract just the text for merging, ignore topics for merged chunks
            chunk_texts = [chunk[0] for chunk in chunks]
            merged_chunk_texts = self.merge_chunks_with_context(chunk_texts)
            # No topic for merged chunks
            merged_chunks = [(merged_text, None) for merged_text in merged_chunk_texts]
        else:
            logger.info("Contextual merging disabled, using manual splitting only")
            merged_chunks = chunks
        
        # Step 3: Final token limit check and splitting if necessary
        final_chunks = []
        for chunk_text, topic in merged_chunks:
            if self.count_tokens(chunk_text) > self.config.max_tokens:
                # Split oversized chunks
                paragraphs = self.split_by_paragraphs(chunk_text)
                # Only preserve topic if this was an original article chunk (not merged)
                for paragraph in paragraphs:
                    final_chunks.append((paragraph, topic))
            else:
                final_chunks.append((chunk_text, topic))
        
        # Step 4: Create Document objects with preserved and enhanced metadata
        documents = []
        for i, (chunk, topic) in enumerate(final_chunks):
            # Merge original metadata with chunk-specific metadata
            doc_metadata = {
                **original_metadata,  # Preserve original metadata (source, page, etc.)
                "chunk_index": i,
                "chunk_tokens": self.count_tokens(chunk),
                "original_document_length": len(text),
                "total_chunks": len(final_chunks),
                "topic": topic if topic else ""
            }
                            
            documents.append(Document(page_content=chunk, metadata=doc_metadata))
        
        logger.info(f"Created {len(documents)} final chunks")
        return documents

    def extract_topic_from_article(self, article_text: str) -> str:
        """
        Extract the topic from an article (second line after Article number)
        
        Args:
            article_text: The full article text
            
        Returns:
            str: The topic/title of the article, or empty string if not found
        """
        lines = article_text.strip().split('\n')
        
        # Remove empty lines and get non-empty lines
        non_empty_lines = [line.strip() for line in lines if line.strip()]
        
        # Simply take the second line as the topic
        if len(non_empty_lines) >= 2:
            return non_empty_lines[1].strip()
        
        return ""

# Modified convenience function to work with PyPDF documents
def process_legal_document_from_pdf(
    file_path: str,
    max_tokens: int = 1000,
    ollama_model: str = "gemma3:27b",
    page_index: int = 0  # Which page to process (default: first page)
) -> List[Document]:
    """
    Convenience function to process a legal document from PDF
    
    Args:
        file_path: Path to the PDF file
        max_tokens: Maximum tokens per chunk
        ollama_model: Ollama model to use for contextual merging
        page_index: Which page to process (0 for first page, -1 for all pages combined)
    
    Returns:
        List[Document]: List of chunked Document objects
    """
    config = ChunkConfig(
        max_tokens=max_tokens,
        ollama_model=ollama_model
    )
    
    chunker = LegalDocumentChunker(config)
    
    # Load the PDF
    loader = PyPDFLoader(str(file_path))
    documents = loader.load()
    
    if not documents:
        logger.warning("No documents loaded from PDF")
        return []
    
    if page_index == -1:
        # Combine all pages into one document
        combined_text = "\n\n".join([doc.page_content for doc in documents])
        combined_metadata = {
            "source": file_path,
            "total_pages": len(documents),
            "pages_combined": "all"
        }
        combined_doc = Document(page_content=combined_text, metadata=combined_metadata)
        return chunker.chunk_document(combined_doc)
    else:
        # Process specific page
        if page_index >= len(documents):
            logger.error(f"Page index {page_index} out of range. Document has {len(documents)} pages.")
            return []
        
        return chunker.chunk_document(documents[page_index])

def process_single_document(
    document: Document,
    max_tokens: int = 1000,
    ollama_model: str = "gemma3:27b"
) -> List[Document]:
    """
    Process a single Document object (most common use case)
    
    Args:
        document: A Document object from PyPDFLoader
        max_tokens: Maximum tokens per chunk
        ollama_model: Ollama model to use for contextual merging
    
    Returns:
        List[Document]: List of chunked Document objects
    """
    config = ChunkConfig(
        max_tokens=max_tokens,
        ollama_model=ollama_model
    )
    
    chunker = LegalDocumentChunker(config)
    return chunker.chunk_document(document)

# Example usage with PyPDF
if __name__ == "__main__":
    # Example 1: Process from PDF file
    file_path = "./docs/اللائحة-التنفيذية-لقانون-الموارد-البشرية-باللغة-الإنجليزية EN.pdf"
    chunks = process_legal_document_from_pdf(
        file_path=file_path,
        max_tokens=500,
        ollama_model="gemma3:27b",
        page_index=0  # Process first page
    )
    
    # Example 2: Process a single document (your use case)
    loader = PyPDFLoader(str(file_path))
    documents = loader.load()
    
    if documents:
        # Process the first document
        chunks = process_single_document(
            document=documents[0],
            max_tokens=500,
            ollama_model="gemma3:27b"
        )
        
        # Print results
        for i, doc in enumerate(chunks):
            print(f"Chunk {i + 1}:")
            print(f"Tokens: {doc.metadata['chunk_tokens']}")
            print(f"Source: {doc.metadata.get('source', 'N/A')}")
            print(f"Page: {doc.metadata.get('page', 'N/A')}")
            print(f"Content: {doc.page_content[:200]}...")
            print("-" * 50)