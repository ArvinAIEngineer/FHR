import sys
import json
from pathlib import Path
from typing import List
import os
# Import the pipeline class
from chromadb_vectorstore import DocumentIngestionPipeline
os.environ['NO_PROXY'] = '10.254.115.17, 10.254.140.69'

class VectorStoreTestSuite:
    def __init__(self, pipeline: DocumentIngestionPipeline):
        self.pipeline = pipeline
    
    def test_basic_search(self, query: str, k: int = 5):
        """Test basic similarity search"""
        print(f"\n{'='*50}")
        print(f"BASIC SEARCH TEST")
        print(f"Query: {query}")
        print(f"{'='*50}")
        
        try:
            results = self.pipeline.search_similar(query, k=k)
            
            if not results:
                print("No results found.")
                return
            
            for i, doc in enumerate(results, 1):
                print(f"\n--- Result {i} ---")
                print(f"Source: {doc.metadata.get('source', 'Unknown')}")
                print(f"Page: {doc.metadata.get('page', 'Unknown')}")
                print(f"Content Preview: {doc.page_content[:200]}...")
                if len(doc.page_content) > 200:
                    print("(Content truncated)")
                    
        except Exception as e:
            print(f"Error in basic search: {e}")
    
    def test_search_with_scores(self, query: str, k: int = 5):
        """Test similarity search with scores"""
        print(f"\n{'='*50}")
        print(f"SEARCH WITH SCORES TEST")
        print(f"Query: {query}")
        print(f"{'='*50}")
        
        try:
            results = self.pipeline.search_with_score(query, k=k)
            
            if not results:
                print("No results found.")
                return
            
            for i, (doc, score) in enumerate(results, 1):
                print(f"\n--- Result {i} (Score: {score:.4f}) ---")
                print(f"Source: {doc.metadata.get('source', 'Unknown')}")
                print(f"Page: {doc.metadata.get('page', 'Unknown')}")
                print(f"Content Preview: {doc.page_content[:150]}...")
                
        except Exception as e:
            print(f"Error in scored search: {e}")
    
    def test_multilingual_search(self, test_queries):

        print(f"\n{'='*50}")
        print(f"MULTILINGUAL SEARCH TEST")
        print(f"{'='*50}")
        
        for query in test_queries:
            print(f"\nTesting query: {query}")
            try:
                results = self.pipeline.search_similar(query, k=3)
                print(f"Found {len(results)} results")
                
                if results:
                    # Show first result preview
                    first_result = results[0]
                    print(f"Top result from: {first_result.metadata.get('file_name', 'Unknown')}")
                    print(f"Preview: {first_result.page_content[:100]}...")
                else:
                    print("No results found for this query")
                    
            except Exception as e:
                print(f"Error searching for '{query}': {e}")
    
    def test_retriever_functionality(self, test_query):
        """Test retriever for RAG applications"""
        print(f"\n{'='*50}")
        print(f"RETRIEVER FUNCTIONALITY TEST")
        print(f"{'='*50}")
        
        try:
            # Get retriever
            retriever = self.pipeline.get_retriever(k=3)
            
            # Test query
            # test_query = "document processing and analysis"
            print(f"Testing retriever with query: {test_query}")
            
            retrieved_docs = retriever.get_relevant_documents(test_query)
            
            print(f"Retrieved {len(retrieved_docs)} documents")
            
            for i, doc in enumerate(retrieved_docs, 1):
                print(f"\n--- Retrieved Document {i} ---")
                print(f"Source: {doc.metadata.get('source', 'Unknown')}")
                print(f"Content: {doc.page_content} ")
                
        except Exception as e:
            print(f"Error testing retriever: {e}")
    
    def test_database_stats(self):
        """Display database statistics"""
        print(f"\n{'='*50}")
        print(f"DATABASE STATISTICS")
        print(f"{'='*50}")
        
        try:
            # Get collection info
            collection = self.pipeline.vector_store._collection
            print(f"Collection name: {collection.name}")
            print(f"Number of documents: {collection.count()}")
            
            # Test a simple query to check if DB is working
            test_results = self.pipeline.search_similar("test", k=1)
            if test_results:
                print("✓ Database is accessible and contains data")
            else:
                print("⚠ Database is accessible but may be empty")
                
        except Exception as e:
            print(f"Error getting database stats: {e}")
    
    def test_folder_ingestion(self, folder_path: str):
        """Test folder ingestion functionality"""
        print(f"\n{'='*50}")
        print(f"FOLDER INGESTION TEST")
        print(f"Folder: {folder_path}")
        print(f"{'='*50}")
        
        try:
            num_chunks = self.pipeline.ingest_folder(folder_path, recursive=True)
            print(f"Successfully ingested {num_chunks} chunks from folder")
            
            if num_chunks > 0:
                print("✓ Folder ingestion completed successfully")
            else:
                print("⚠ No documents found or processed in folder")
                
        except Exception as e:
            print(f"Error in folder ingestion: {e}")
    
    def interactive_search(self):
        """Interactive search mode"""
        print(f"\n{'='*50}")
        print(f"INTERACTIVE SEARCH MODE")
        print(f"Enter 'quit' to exit")
        print(f"{'='*50}")
        
        while True:
            try:
                query = input("\nEnter your search query: ").strip()
                
                if query.lower() in ['quit', 'exit', 'q']:
                    break
                
                if not query:
                    continue
                
                # results = self.pipeline.search_with_score(query, k=3)
                results = self.test_retriever_functionality(query)
                
                if not results:
                    print("No results found.")
                    continue
                
                print(f"\nFound {len(results)} results:")
                for i, (doc, score) in enumerate(results, 1):
                    print(f"\n{i}. Score: {score:.4f}")
                    print(f"   Source: {doc.metadata.get('file_name', 'Unknown')}")
                    print(f"   Content: {doc.page_content}")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")


def main():
    """Main test function"""
    print("Document Ingestion Pipeline Test Suite")
    print("=" * 50)
    
    # Initialize pipeline
    try:
        pipeline = DocumentIngestionPipeline(
            persist_directory="./multilingual_chroma_db"
        )
        print("✓ Pipeline initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize pipeline: {e}")
        return
    
    # Initialize test suite
    test_suite = VectorStoreTestSuite(pipeline)
    
    # Run tests
    test_suite.test_database_stats()
    
    # Test folder ingestion if folder provided
    test_folder = input("\nEnter path to test folder (or press Enter to skip): ").strip()
    if test_folder and Path(test_folder).exists():
        test_suite.test_folder_ingestion(test_folder)
    
    # Test with sample queries
    sample_queries = [
            "UAE national employees working for the Federal Government shall be eligible for children social allowance at"
    ]
    
    for query in sample_queries:
        test_suite.test_basic_search(query, k=3)
    
    # Test multilingual capabilities
    test_suite.test_multilingual_search(sample_queries)
    
    # Test retriever functionality
    # test_suite.test_retriever_functionality()
    
    # Ask user if they want interactive mode
    response = input("\nWould you like to try interactive search? (y/n): ")
    if response.lower().startswith('y'):
        test_suite.interactive_search()
    
    print("\nTest suite completed!")


if __name__ == "__main__":
    main()