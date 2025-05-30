# Module for interacting with ChromaDB for vector storage and similarity search.
import chromadb
import os
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import numpy as np

# Configuration constants for ChromaDB.
# COLLECTION_NAME = "car-manuals"  # Default, but we'll make it flexible
PERSIST_DIRECTORY = "chroma_db"    # Directory where ChromaDB data will be persisted.
DEFAULT_COLLECTION_NAME = "car-manuals" # Keep a default

def get_client():
    """Initializes and returns a persistent ChromaDB client."""
    return chromadb.PersistentClient(path=PERSIST_DIRECTORY, settings=Settings())

def get_collection(collection_name: str, client: Optional[chromadb.ClientAPI] = None):
    """Initialize ChromaDB client with persistence and get or create the specified collection.
    
    Args:
        collection_name (str): The name of the collection to get or create.
        client (Optional[chromadb.ClientAPI]): An existing client to use. If None, a new one is created.

    Returns:
        chromadb.api.models.Collection.Collection: The ChromaDB collection object.
    """
    if client is None:
        client = get_client()
    
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}  # Specifies the distance metric for similarity search.
    )
    return collection

# Modified store_embeddings to accept collection_name and pre-generated IDs
def store_embeddings(texts: List[str], 
                     embeddings: List[List[float]], 
                     ids: List[str], 
                     collection_name: str, 
                     metadata: List[Dict[str, Any]] = None):
    """Store text chunks, their embeddings, IDs, and metadata in a specified ChromaDB collection.

    Args:
        texts (List[str]): A list of text chunks to store.
        embeddings (List[List[float]]): A list of embeddings corresponding to the text chunks.
        ids (List[str]): A list of unique IDs for each document.
        collection_name (str): The name of the ChromaDB collection to use.
        metadata (List[Dict[str, Any]], optional): A list of metadata dictionaries for each text chunk.
                                                  Defaults to None, in which case basic metadata is generated.

    Returns:
        dict: A dictionary containing the count of stored items and the collection name.
    """
    if not (len(texts) == len(embeddings) == len(ids) == (len(metadata) if metadata else len(texts))):
        raise ValueError("texts, embeddings, ids, and metadata (if provided) must have the same number of elements.")

    collection = get_collection(collection_name) # Get the specified collection.
    
    # If no metadata is provided, create a default metadata structure for each document.
    # This ensures metadata list aligns with other lists if it was None.
    processed_metadata = metadata if metadata is not None else [{"source": "unknown"} for _ in texts]
        
    # Add documents to the collection in batches to handle potentially large datasets efficiently.
    batch_size = 100
    for i in range(0, len(texts), batch_size):
        batch_end = min(i + batch_size, len(texts)) # Ensure the batch end does not exceed the list length.
        collection.upsert(
            ids=ids[i:batch_end],
            embeddings=embeddings[i:batch_end],
            documents=texts[i:batch_end],
            metadatas=processed_metadata[i:batch_end]
        )
    
    return {
        "stored_count": len(texts),
        "collection_name": collection_name
    }

# Modified search_similar to accept collection_name
def search_similar(query_embedding: List[float], collection_name: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """Search for documents in a specified ChromaDB collection that are most similar to a given query embedding.

    Args:
        query_embedding (List[float]): The embedding of the query string.
        collection_name (str): The name of the ChromaDB collection to search in.
        top_k (int, optional): The number of top similar documents to retrieve. Defaults to 3.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries, where each dictionary represents a similar document
                              and includes its text, similarity score, and metadata.
    """
    collection = get_collection(collection_name) # Get the specified collection.
    
    # Query the collection for the most similar documents.
    # 'include' specifies what information to return along with the documents.
    results = collection.query(
        query_embeddings=[query_embedding], # The query embedding needs to be in a list.
        n_results=top_k,
        include=["documents", "distances", "metadatas"] # Request documents, distances, and metadatas.
    )
    
    # Format the raw results from ChromaDB into a more usable list of dictionaries.
    similar_chunks = []
    if results['documents'] and results['documents'][0]: # Check if results are not empty.
        for i in range(len(results['documents'][0])):
            # Ensure distances are available before calculating similarity
            similarity_score = 1 - results['distances'][0][i] if results.get('distances') and results['distances'][0] and i < len(results['distances'][0]) else None # Renamed for clarity
            similar_chunks.append({
                'text': results['documents'][0][i],
                'similarity': similarity_score,
                'metadata': results['metadatas'][0][i]
            })
    
    return similar_chunks

# Keep the old init_chroma for now if other parts of the code still use it with the default name,
# but ideally, they should be updated to use get_collection.
# For new code, always use get_collection(collection_name).
def init_chroma():
    """Initialize ChromaDB client with persistence and get or create the DEFAULT collection.
    DEPRECATED for new features. Use get_collection(collection_name) instead.
    Returns:
        chromadb.api.models.Collection.Collection: The ChromaDB collection object.
    """
    print("Warning: init_chroma() is deprecated for new features. Use get_collection(collection_name).")
    return get_collection(DEFAULT_COLLECTION_NAME) 