# Handles PDF processing: text extraction, chunking, and validation.
import PyPDF2
import json # Not directly used, but PyPDF2 might interact with JSON-like structures.
import os
from storage_utils import save_chunks_to_json
from typing import Dict, List

def validate_chunk(chunk: str) -> bool:
    """Validates if a text chunk is meaningful (e.g., min 10 words).

    Args:
        chunk: The text chunk to validate.

    Returns:
        True if the chunk is valid, False otherwise.
    """
    # Basic check for minimum word count.
    if len(chunk.split()) < 10: # Arbitrary minimum word count.
        return False
    return True

def chunk_text_by_word_count(text: str, target_chunk_words: int = 250, overlap_words: int = 50) -> List[str]:
    """Splits text into chunks by word count with overlap, ensuring full text coverage.

    Args:
        text: The input text to be chunked.
        target_chunk_words: The desired number of words per chunk.
        overlap_words: The number of words to overlap between consecutive chunks.

    Returns:
        A list of text chunks.
    """
    
    words = text.split()
    if not words:
        return []

    chunks = []
    current_pos = 0
    # Iterate through the words to create chunks.
    while current_pos < len(words):
        start_pos = current_pos
        end_pos = min(current_pos + target_chunk_words, len(words))
        chunk_list = words[start_pos:end_pos]
        chunks.append(" ".join(chunk_list))
        
        # Advance current_pos by the target chunk size minus the overlap.
        current_pos += (target_chunk_words - overlap_words)
        
        # Special handling for the end of the text to ensure the last part is included.
        if current_pos >= len(words) - overlap_words and end_pos < len(words):
            # If the remaining text is less than or equal to the target chunk size,
            # and it's not already the last chunk created, add it as a new chunk.
            if len(words) - start_pos <= target_chunk_words:
                 if words[start_pos:] != chunk_list: # Avoid duplicate final chunk.
                    chunks.append(" ".join(words[start_pos:]))
                 break # Exit loop as the entire text has been processed.
        elif end_pos == len(words):
            # If the end_pos reaches the end of the words list, it means the last chunk is formed.
            break
            
    # Fallback to capture the very last segment if it was missed by the primary loop logic.
    # This can happen if the remaining text is smaller than the overlap.
    if chunks:
        last_chunk_words = chunks[-1].split()
        # Check if there are words in the text and the last chunk is not empty,
        # and the last word of the text is different from the last word of the last chunk.
        if words and last_chunk_words and words[-1] != last_chunk_words[-1]:
            # Define the start of the potential new chunk, ensuring it's within bounds.
            final_chunk_start = max(0, len(words) - target_chunk_words)
            potential_new_chunk = " ".join(words[final_chunk_start:])
            # Add the potential new chunk if it's different from the last chunk already added.
            if chunks[-1] != potential_new_chunk: # Avoid exact duplication.
                    chunks.append(potential_new_chunk)

    return [chunk for chunk in chunks if chunk.strip()] # Filter out empty strings.


def process_pdf(pdf_path: str) -> Dict:
    """Extracts text from PDF, chunks, validates, and saves to JSON.

    Args:
        pdf_path: The path to the PDF file.

    Returns:
        A dictionary containing processing results, including the number of pages,
        number of chunks, and the output file path.
    """
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        num_pages = len(reader.pages)
        all_text = ""

        # Extract text from each page.
        for page_num in range(num_pages):
            page_text = reader.pages[page_num].extract_text()
            if page_text:
                all_text += page_text + "\n" # Newline as page separator.
        
        # Chunk the extracted text.
        text_chunks = chunk_text_by_word_count(all_text, target_chunk_words=250, overlap_words=50)
        
        chunks_data = []
        # Approximate page number for each chunk.
        # This is a best-effort calculation.
        chunks_per_page_approx = 0
        if num_pages > 0 and len(text_chunks) > 0:
            chunks_per_page_approx = max(1, len(text_chunks) // num_pages)

        for i, chunk_text in enumerate(text_chunks):
            if validate_chunk(chunk_text):
                page_number_for_chunk = 1 # Default page number.
                if chunks_per_page_approx > 0:
                    # Calculate page index based on approximate chunks per page.
                    page_idx = i // chunks_per_page_approx
                    page_number_for_chunk = page_idx + 1 
                elif num_pages > 0:
                    # If approximation is not possible, assign sequentially up to num_pages.
                    page_number_for_chunk = min(i + 1, num_pages)
                else: 
                    page_number_for_chunk = 0 # Indicates no pages or invalid PDF.

                if num_pages > 0:
                    # Ensure page number does not exceed the actual number of pages.
                    page_number_for_chunk = min(page_number_for_chunk, num_pages)
                
                chunks_data.append({
                    "id": f"chunk_{i+1}",
                    "text": chunk_text,
                    "page_number": str(page_number_for_chunk) if page_number_for_chunk > 0 else "N/A"
                })
            else:
                # Log skipped chunks for debugging or information.
                print(f"Skipping invalid chunk {i+1} (too short/not alphanumeric).")

    # Save the processed chunks to a JSON file.
    output_file = save_chunks_to_json(chunks_data, source_pdf=pdf_path)
    
    return {
        "message": "PDF processed, chunks saved to JSON.",
        "num_pages": num_pages,
        "num_chunks": len(chunks_data),
        "output_file": output_file
    } 