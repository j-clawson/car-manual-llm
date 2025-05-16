# Module for interacting with ChromaDB for vector storage and similarity search.
import chromadb
import os
from chromadb.config import Settings
from typing import List, Dict, Any
import numpy as np

# Configuration constants for ChromaDB.
COLLECTION_NAME = "car-manuals"  # Name of the collection in ChromaDB.
PERSIST_DIRECTORY = "chroma_db"    # Directory where ChromaDB data will be persisted.

def init_chroma():
    """Initialize ChromaDB client with persistence and get or create the collection.
    
    Returns:
        chromadb.api.models.Collection.Collection: The ChromaDB collection object.
    """
    # Create a persistent ChromaDB client.
    # The database will be stored in the PERSIST_DIRECTORY.
    client = chromadb.PersistentClient(path=PERSIST_DIRECTORY, settings=Settings())
    
    # Get an existing collection or create a new one if it doesn't exist.
    # The collection is configured to use cosine similarity for searching.
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}  # Specifies the distance metric for similarity search.
    )
    
    return collection

def store_embeddings(texts: List[str], embeddings: List[List[float]], metadata: List[Dict[str, Any]] = None):
    """Store text chunks, their embeddings, and metadata in ChromaDB.

    Args:
        texts (List[str]): A list of text chunks to store.
        embeddings (List[List[float]]): A list of embeddings corresponding to the text chunks.
        metadata (List[Dict[str, Any]], optional): A list of metadata dictionaries for each text chunk.
                                                  Defaults to None, in which case basic metadata is generated.

    Returns:
        dict: A dictionary containing the count of stored items and the collection name.
    """
    collection = init_chroma() # Initialize or get the collection.
    
    # Generate unique IDs for the documents to be stored.
    # These IDs are required by ChromaDB.
    ids = [f"doc_{i}" for i in range(len(texts))]
    
    # If no metadata is provided, create a default metadata structure for each document.
    if metadata is None:
        metadata = [{"source": "unknown"} for _ in texts]
    
    # Add documents to the collection in batches to handle potentially large datasets efficiently.
    batch_size = 100
    for i in range(0, len(texts), batch_size):
        batch_end = min(i + batch_size, len(texts)) # Ensure the batch end does not exceed the list length.
        collection.add(
            ids=ids[i:batch_end],
            embeddings=embeddings[i:batch_end],
            documents=texts[i:batch_end],
            metadatas=metadata[i:batch_end]
        )
    
    return {
        "stored_count": len(texts),
        "collection_name": COLLECTION_NAME
    }

def search_similar(query_embedding: List[float], top_k: int = 3) -> List[Dict[str, Any]]:
    """Search for documents in ChromaDB that are most similar to a given query embedding.

    Args:
        query_embedding (List[float]): The embedding of the query string.
        top_k (int, optional): The number of top similar documents to retrieve. Defaults to 3.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries, where each dictionary represents a similar document
                              and includes its text, similarity score, and metadata.
    """
    collection = init_chroma() # Initialize or get the collection.
    
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
            similarity = 1 - results['distances'][0][i] if results.get('distances') and results['distances'][0] and i < len(results['distances'][0]) else None
            similar_chunks.append({
                'text': results['documents'][0][i],
                'similarity': similarity,
                'metadata': results['metadatas'][0][i]
            })
    
    return similar_chunks 