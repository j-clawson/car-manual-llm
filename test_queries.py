# This script provides a command-line interface to test querying the ChromaDB vector store.
# It allows users to input a query, generates an embedding for it, and retrieves similar documents.
import json
from embeddings import get_embedding_for_query # Function to generate query embeddings.
from chroma_store import search_similar # Function to search ChromaDB for similar documents.

def run_test_query(query_text: str, top_k: int = 3):
    """
    Executes a test query against the ChromaDB vector store.
    
    It performs the following steps:
    1. Generates an embedding for the `query_text` using `get_embedding_for_query`.
    2. Searches ChromaDB for the `top_k` most similar documents using `search_similar`.
    3. Prints the query, the number of results found, and details of each result (text, similarity, metadata).

    Args:
        query_text (str): The natural language query to test.
        top_k (int, optional): The number of top similar results to retrieve. Defaults to 3.
    """
    print(f"\n--- Testing Query ---")
    print(f"Query: \"{query_text}\"")
    print(f"Requesting top {top_k} results.")
    
    # Step 1: Generate embedding for the query.
    try:
        print("\nGenerating embedding for the query...")
        query_embedding = get_embedding_for_query(query_text)
        if not query_embedding:
            print("Failed to generate query embedding (embedding was empty).")
            return
        print(f"Successfully generated embedding for the query (dimension: {len(query_embedding)}).")
    except Exception as e:
        print(f"Error generating query embedding: {e}")
        return # Exit if embedding generation fails.

    # Step 2: Search for similar chunks in ChromaDB.
    try:
        print("\nSearching for similar documents in ChromaDB...")
        results = search_similar(query_embedding, top_k)
        print(f"\n--- Search Results ---")
        print(f"Found {len(results)} result(s) for query: \"{query_text}\"")
        
        if results:
            for i, result in enumerate(results):
                print(f"\n--- Result {i+1} ---")
                # Ensure text is handled well, especially if it contains newlines or is very long.
                text_content = str(result.get('text', 'N/A'))
                # For display, replace newlines and limit length if necessary.
                display_text = text_content.replace('\n', ' \n  ') 
                if len(display_text) > 300: # Truncate long texts for readability.
                    display_text = display_text[:297] + "..."
                print(f"  Text: {display_text}")
                
                similarity_score = result.get('similarity')
                if similarity_score is not None:
                    print(f"  Similarity: {similarity_score:.4f}")
                else:
                    print(f"  Similarity: N/A (Score not provided)")
                    
                print(f"  Metadata: {result.get('metadata', {})}")
                print("-" * 30) # Separator for better readability
        else:
            print("No results found in ChromaDB for this query.")
            
    except Exception as e:
        print(f"Error searching ChromaDB: {e}")

# This block executes when the script is run directly.
if __name__ == "__main__":
    # --- Configuration for the test query ---
    # You can change the sample_query and number_of_results here to test different scenarios.
    
    sample_query = "How do I change the oil?" 
    # sample_query = "What are the safety features described in the manual?"
    # sample_query = "Tell me about the infotainment system and its connectivity options."
    # sample_query = "What is the recommended tire pressure?"
    
    number_of_results = 3  # Specify how many top results you want to retrieve.
    # -------------------------------------------
    
    print("Starting test query script...")
    run_test_query(sample_query, top_k=number_of_results)
    print("\nTest query script finished.") 