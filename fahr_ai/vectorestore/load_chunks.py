from pathlib import Path
from datetime import datetime
from chromadb_vectorstore import DocumentIngestionPipeline
# Assuming your DocumentIngestionPipeline class is imported or defined above

def load_and_save_chunks(
    persist_directory: str = "./chroma_db_backup",
    ollama_base_url: str = "http://10.254.140.69:11434",
    embedding_model: str = "nomic-embed-text:latest",
    output_file: str = "chunks_output.txt",
    num_chunks: int = 10
):
    """
    Load database, retrieve chunks, and save to text file
    
    Args:
        persist_directory: Directory where ChromaDB is persisted
        ollama_base_url: Base URL for Ollama server
        embedding_model: Embedding model name
        output_file: Output text file name
        num_chunks: Number of chunks to retrieve
    """
    
    try:
        # Initialize the pipeline (this will load the existing database)
        pipeline = DocumentIngestionPipeline(
            ollama_base_url=ollama_base_url,
            embedding_model=embedding_model,
            persist_directory=persist_directory
        )
        
        print(f"Successfully loaded database from: {persist_directory}")
        
        # Get the collection from the vector store
        collection = pipeline.vector_store._collection
        
        # Get all documents (limited to num_chunks)
        results = collection.get(limit=num_chunks)
#         results = collection.get(
#                 where={"source": {"$eq": "docs/قانون الموارد البشرية في الحكومة الاتحاديةAR.pdf"}},  # Adjust key based on your metadata
#                 limit=num_chunks
# )
        if not results['documents']:
            print("No documents found in the database.")
            return
        
        print(f"Retrieved {len(results['documents'])} chunks from database")
        
        # Prepare content for saving
        output_content = []
        output_content.append("=" * 80)
        output_content.append(f"CHUNKS EXTRACTED FROM DATABASE")
        output_content.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output_content.append(f"Database location: {persist_directory}")
        output_content.append(f"Number of chunks: {len(results['documents'])}")
        output_content.append("=" * 80)
        output_content.append("")
        
        # Process each chunk
        for i, (doc, metadata, doc_id) in enumerate(zip(
            results['documents'], 
            results['metadatas'], 
            results['ids']
        ), 1):
            output_content.append(f"CHUNK {i}")
            output_content.append("-" * 40)
            output_content.append(f"Document ID: {doc_id}")
            
            # Add metadata if available
            if metadata:
                output_content.append("Metadata:")
                for key, value in metadata.items():
                    output_content.append(f"  {key}: {value}")
            
            output_content.append("")
            output_content.append("Content:")
            output_content.append(doc)
            output_content.append("")
            output_content.append("=" * 80)
            output_content.append("")
        
        # Save to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(output_content))
        
        print(f"Successfully saved {len(results['documents'])} chunks to: {output_file}")
        
        # Print summary
        print("\nSummary:")
        print(f"- Database location: {persist_directory}")
        print(f"- Chunks retrieved: {len(results['documents'])}")
        print(f"- Output file: {output_file}")
        print(f"- File size: {Path(output_file).stat().st_size} bytes")
        
    except Exception as e:
        print(f"Error loading database or saving chunks: {str(e)}")
        print("Please make sure:")
        print("1. The database directory exists and contains valid ChromaDB data")
        print("2. Ollama server is running and accessible")
        print("3. The embedding model is available")

# Alternative method using similarity search (if you want to search for specific content)
def load_and_save_chunks_with_query(
    query: str = "",
    persist_directory: str = "./chroma_db_backup",
    ollama_base_url: str = "http://10.254.140.69:11434",
    embedding_model: str = "nomic-embed-text:latest",
    output_file: str = "chunks_query_output.txt",
    num_chunks: int = 10
):
    """
    Load database, search for similar chunks, and save to text file
    
    Args:
        query: Search query (empty string will get random chunks)
        persist_directory: Directory where ChromaDB is persisted
        ollama_base_url: Base URL for Ollama server
        embedding_model: Embedding model name
        output_file: Output text file name
        num_chunks: Number of chunks to retrieve
    """
    
    try:
        # Initialize the pipeline
        pipeline = DocumentIngestionPipeline(
            ollama_base_url=ollama_base_url,
            embedding_model=embedding_model,
            persist_directory=persist_directory
        )
        
        print(f"Successfully loaded database from: {persist_directory}")
        
        if query:
            # Search for similar documents
            docs = pipeline.vector_store.similarity_search(query, k=num_chunks)
            print(f"Found {len(docs)} chunks similar to query: '{query}'")
        else:
            # Get random documents
            collection = pipeline.vector_store._collection
            results = collection.get(limit=num_chunks)
            docs = [type('Document', (), {'page_content': content, 'metadata': meta})() 
                   for content, meta in zip(results['documents'], results['metadatas'])]
            print(f"Retrieved {len(docs)} random chunks")
        
        # Save to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("CHUNKS FROM DATABASE\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Database location: {persist_directory}\n")
            if query:
                f.write(f"Query: {query}\n")
            f.write(f"Number of chunks: {len(docs)}\n")
            f.write("=" * 80 + "\n\n")
            
            for i, doc in enumerate(docs, 1):
                f.write(f"CHUNK {i}\n")
                f.write("-" * 40 + "\n")
                if hasattr(doc, 'metadata') and doc.metadata:
                    f.write("Metadata:\n")
                    for key, value in doc.metadata.items():
                        f.write(f"  {key}: {value}\n")
                f.write("\nContent:\n")
                f.write(doc.page_content + "\n")
                f.write("\n" + "=" * 80 + "\n\n")
        
        print(f"Successfully saved {len(docs)} chunks to: {output_file}")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    # Method 1: Load first 10 chunks from database
    print("Loading chunks sample from database...")
    load_and_save_chunks(
        persist_directory="./contextAware_chroma_db_1",
        output_file="chunks_smaple.txt",
        num_chunks=700
    )
    
    # Method 2: Search for chunks related to a specific query (optional)
    # print("\nSearching for chunks with specific query...")
    # load_and_save_chunks_with_query(
    #     query="your search query here",
    #     persist_directory="./chroma_db_backup",
    #     output_file="query_chunks.txt",
    #     num_chunks=10
    # )