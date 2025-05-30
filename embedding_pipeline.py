# This module defines the pipeline for generating and storing embeddings for processed documents.
import json
import os
from typing import List, Dict
from embeddings import create_embeddings # Function to create embeddings from text.
from chroma_store import store_embeddings, DEFAULT_COLLECTION_NAME # Function to store embeddings in ChromaDB and get default name.
from datetime import datetime # For timestamping metadata.

def process_json_for_embeddings(json_path: str, collection_name: str) -> Dict:
    """Processes a JSON file containing text chunks, generates embeddings for these chunks,
    and stores them in the specified ChromaDB vector store collection.

    Args:
        json_path (str): Path to the JSON file containing text chunks.
        collection_name (str): Name of the ChromaDB collection to store embeddings in.

    Returns:
        A dictionary summarizing the embedding process, including input/output file paths,
        number of embeddings generated, and embedding dimension.
    """
    # Load data from the JSON file.
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    # Extract text content from each chunk.
    texts = [chunk['text'] for chunk in data['chunks']]
    # Prepare metadata for each chunk, including source PDF, chunk index, and timestamp.
    metadata = [{
        'source': data['source_pdf'], 
        'chunk_index': i,
        'original_text_id': chunk.get('id', f'chunk_{i}'), # Use original chunk ID if available, else generate
        'timestamp': datetime.now().isoformat()
    } for i, chunk in enumerate(data['chunks'])] # Iterate with chunk for original_text_id
    
    # Generate unique IDs for ChromaDB for each chunk
    # It's good practice for these to be stable and unique.
    # Using a combination of source PDF and chunk index or original chunk ID.
    chroma_ids = [
        f"pdf_{os.path.basename(data['source_pdf'])}_{meta['original_text_id']}_{i}" 
        for i, meta in enumerate(metadata)
    ]

    # Generate embeddings for the extracted texts.
    embeddings_data = create_embeddings(texts)

    if not embeddings_data or len(texts) != len(embeddings_data) or len(texts) != len(chroma_ids) or len(texts) != len(metadata):
        # Handle error: mismatch in list lengths or no embeddings generated
        error_msg = "Mismatch in data lengths or no embeddings generated. Cannot store."
        print(f"Error in process_json_for_embeddings: {error_msg}")
        # Optionally, return an error structure or raise an exception
        return {
            "input_file": json_path,
            "output_file": None, 
            "num_embeddings": 0,
            "embedding_dimension": 0,
            "message": error_msg,
            "error": True
        }

    # Store the generated embeddings along with their texts and metadata in ChromaDB.
    store_embeddings(
        texts=texts, 
        embeddings=embeddings_data,
        ids=chroma_ids, 
        collection_name=collection_name,
        metadata=metadata
    )
    
    output_file_basename = os.path.basename(json_path).split('.')[0]
    output_file = os.path.join('embedded_data', f"{output_file_basename}_embedded.json")
    os.makedirs('embedded_data', exist_ok=True) # Ensure the directory exists.
    
    with open(output_file, 'w') as f:
        json.dump({"status": "embeddings_generated", "source_json": json_path, "collection": collection_name}, f)

    return {
        "input_file": json_path,
        "output_file": output_file, 
        "num_embeddings": len(embeddings_data) if embeddings_data else 0,
        "embedding_dimension": len(embeddings_data[0]) if embeddings_data and embeddings_data[0] else 0,
        "message": f"Successfully generated and stored embeddings in ChromaDB collection '{collection_name}'"
    }

def get_pending_documents() -> List[str]:
    """Identifies processed JSON documents in 'processed_data' that are pending embedding generation.
    This is done by comparing files in 'processed_data' against marker files in 'embedded_data'.
    """
    processed_dir = "processed_data"
    embedded_dir = "embedded_data"
    
    # If the directory for processed data doesn't exist, there are no pending documents.
    if not os.path.exists(processed_dir):
        return []
    
    # Get a set of all JSON files in the processed_data directory.
    processed_files = set(f for f in os.listdir(processed_dir) if f.endswith('.json'))
    
    # Get a set of marker files from embedded_data, adjusting names to match processed_files.
    embedded_files_markers = set()
    if os.path.exists(embedded_dir):
        embedded_files_markers = set(
            f.replace('_embedded.json', '.json') 
            for f in os.listdir(embedded_dir) 
            if f.endswith('_embedded.json')
        )
    
    # The difference between these sets gives the files that are processed but not yet embedded.
    pending_files = list(processed_files - embedded_files_markers)
    return pending_files 