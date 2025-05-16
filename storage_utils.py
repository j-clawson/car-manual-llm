# This module provides utility functions for storing processed data, primarily text chunks from documents.
import json
import os
from typing import List, Dict # For type hinting.
from datetime import datetime # For generating timestamps.

# Directory where processed JSON files will be stored.
PROCESSED_DATA_DIR = "processed_data"

def save_chunks_to_json(chunks: List[Dict], source_pdf: str) -> str:
    """Saves a list of text chunks (and their metadata) to a JSON file.

    Each chunk is expected to be a dictionary. The output JSON file includes
    metadata about the source PDF and the time of processing.

    Args:
        chunks (List[Dict]): A list of dictionaries, where each dictionary represents a chunk
                             of text and its associated metadata (e.g., page number, id).
        source_pdf (str): The path to the original PDF file from which the chunks were extracted.

    Returns:
        str: The path to the created JSON file.
    """
    # Generate a timestamp for the filename to ensure uniqueness.
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create a safe base name for the output file from the source PDF path.
    # This extracts the filename without extension from the source_pdf path.
    base_name = os.path.basename(source_pdf)
    name_part = base_name.split('.')[0] if '.' in base_name else base_name
    
    # Construct the full output file path.
    output_filename = f"{name_part}_{timestamp}.json"
    output_file_path = os.path.join(PROCESSED_DATA_DIR, output_filename)
    
    # Ensure the directory for processed data exists.
    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
    
    # Prepare the data structure to be saved in the JSON file.
    output_data = {
        "source_pdf": source_pdf, # Path to the original source PDF.
        "processing_timestamp": datetime.now().isoformat(), # ISO format timestamp of processing.
        "num_chunks": len(chunks), # Total number of chunks processed.
        "chunks": chunks # The list of chunk data.
    }
    
    # Write the data to the JSON file.
    with open(output_file_path, 'w') as f:
        json.dump(output_data, f, indent=2) # Use indent for pretty printing.
        
    print(f"Successfully saved {len(chunks)} chunks to {output_file_path}")
    return output_file_path

