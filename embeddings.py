# This module is responsible for generating text embeddings using OpenAI's API.
from openai import OpenAI
# import httpx # No longer needed for basic init with openai > 1.x, library handles it.
from typing import List
import os
from time import sleep # Used for adding delays to avoid API rate limits.
from dotenv import load_dotenv # For loading environment variables from a .env file.

# Load environment variables from a .env file in the project root.
# This is where the OPENAI_API_KEY should be stored.
load_dotenv()

# Initialize the OpenAI client.
# The API key is fetched from environment variables (loaded from .env or system env).
# Ensure OPENAI_API_KEY is set in your .env file or system environment variables for this to work.
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

# Default model for embeddings. This can be updated to use other OpenAI embedding models.
EMBEDDING_MODEL = "text-embedding-3-small"

def create_embeddings(texts: List[str], batch_size: int = 100) -> List[List[float]]:
    """
    Generates embeddings for a list of text strings using the specified OpenAI API model.
    Processes texts in batches to manage API rate limits and request sizes effectively.
    """
    if not texts: # Check if the input list is empty.
        print("Input text list is empty. No embeddings will be generated.")
        return []

    all_embeddings = [] # Initialize an empty list to store all generated embeddings.
    
    print(f"\nAttempting to generate embeddings for {len(texts)} text chunks using model '{EMBEDDING_MODEL}'.")
    
    # Process texts in batches to avoid overwhelming the API or hitting request size limits.
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i + batch_size] # Get the current batch of texts.
        current_batch_num = (i // batch_size) + 1
        total_batches = (len(texts) + batch_size - 1) // batch_size # Calculate total number of batches.
        
        try:
            print(f"Processing batch {current_batch_num} of {total_batches} (size: {len(batch_texts)} texts)..._model")
            
            # Call the OpenAI API's embeddings creation endpoint.
            response = client.embeddings.create(
                model=EMBEDDING_MODEL, # Specify the embedding model to use.
                input=batch_texts      # Provide the batch of texts as input.
            )
            
            # Extract the embedding vectors from the API response object.
            # response.data is a list of embedding objects, each having an 'embedding' attribute.
            batch_embeddings = [embedding.embedding for embedding in response.data]
            all_embeddings.extend(batch_embeddings) # Add the generated embeddings for this batch to the main list.
            
            print(f"Successfully generated {len(batch_embeddings)} embeddings for batch {current_batch_num}.")
            
            # Implement a brief pause to respect API rate limits, especially if processing many batches.
            if current_batch_num < total_batches: # Only sleep if there are more batches to process.
                sleep(0.5) # Delay for 0.5 seconds
                
        except Exception as e:
            # Handle exceptions that might occur during the API call for a batch.
            print(f"Error generating embeddings for batch {current_batch_num}: {type(e).__name__} - {str(e)}")
            # For critical errors (e.g., authentication), re-raising might be appropriate.
            raise # Re-raise the exception to be handled by the caller or to stop execution.
            
    print(f"\nCompleted generating {len(all_embeddings)} embeddings in total.")
    return all_embeddings

def get_embedding_for_query(query: str) -> List[float]:
    """
    Generates an embedding for a single query text string using the OpenAI API.
    This is typically used for generating the embedding of a user's search query 
    to compare against document embeddings.
    """
    # Validate that the query string is not empty or just whitespace.
    if not query.strip():
        print("Query string is empty or whitespace. Cannot generate embedding.")
        return [] # Return empty list for an empty query.

    try:
        print(f"Generating embedding for query: '{query[:100]}...'") # Log a snippet of the query for context.
        
        # Call the OpenAI API to create an embedding for the single query string.
        response = client.embeddings.create(
            model=EMBEDDING_MODEL, # Use the configured embedding model.
            input=[query]          
        )
        # The response.data will be a list containing one embedding object.
        if response.data and len(response.data) > 0:
            return response.data[0].embedding
        else:
            print("OpenAI API returned no data for the query embedding.")
            return [] # Should not happen with a valid query and API key

    except Exception as e:
        # Handle exceptions during the API call for the query embedding.
        print(f"Error generating query embedding: {type(e).__name__} - {str(e)}")
        # Propagate the exception for higher-level error handling.
        raise # Re-raise to signal failure to the caller. 