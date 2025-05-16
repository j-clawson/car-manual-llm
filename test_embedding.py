# This script is a simple test to verify that the OpenAI embedding generation is working correctly.
# It calls the `get_embedding_for_query` function with a test string and prints the result.

from embeddings import get_embedding_for_query # The function to test.

def test_embedding_generation():
    """
    Tests the `get_embedding_for_query` function from the `embeddings` module.
    
    It attempts to generate an embedding for a predefined test query string.
    Prints a success message and the embedding dimension if successful, or an error message if it fails.
    """
    test_query = "This is a test query for embedding generation."
    print(f"Attempting to generate embedding for: \"{test_query}\"")
    
    try:
        # Call the function to get an embedding for the test query.
        embedding = get_embedding_for_query(test_query)
        
        if embedding and isinstance(embedding, list) and len(embedding) > 0:
            print("\n--- Test Result ---")
            print("✅ Successfully generated embedding!")
            print(f"   Embedding Dimension: {len(embedding)}")
            # Optionally, print a snippet of the embedding
            # print(f"   Embedding Snippet: {embedding[:5]}...") 
        else:
            print("\n--- Test Result ---")
            print("❌ Failed to generate embedding: The returned embedding was empty or invalid.")
            
    except Exception as e:
        # Catch any exceptions during the embedding generation process.
        print("\n--- Test Result ---")
        print("❌ Failed to generate embedding due to an error!")
        print(f"   Error Type: {type(e).__name__}")
        print(f"   Error Message: {str(e)}")

# This block executes when the script is run directly.
if __name__ == "__main__":
    print("Starting OpenAI embedding generation test...")
    test_embedding_generation()
    print("\nEmbedding generation test finished.") 