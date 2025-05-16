import sys
import multiprocessing
import urllib.parse

# Ensures that multiprocessing works correctly on macOS.
if sys.platform == 'darwin':
    multiprocessing.set_executable(sys.executable)

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel
import os
from document_processor import process_pdf
from embedding_pipeline import process_json_for_embeddings, get_pending_documents
from embeddings import get_embedding_for_query
from chroma_store import search_similar
from typing import List, Optional

# Initialize FastAPI application
app = FastAPI(title="Car Manual RAG System")

# Pydantic model for the response of the PDF processing endpoint.
class ProcessingResponse(BaseModel):
    success: bool
    output_file: str
    metadata: dict
    message: str
    next_embedding_command: Optional[str] = None

# Pydantic model for the response of the embedding generation endpoint.
class EmbeddingResponse(BaseModel):
    success: bool
    input_file: str
    output_file: str
    num_embeddings: int
    embedding_dimension: int
    message: str

# Pydantic model for the search query.
class SearchQuery(BaseModel):
    query: str
    top_k: Optional[int] = 3 # Default to top 3 results if not specified.

# Endpoint to process an uploaded PDF file.
@app.post("/process-pdf", response_model=ProcessingResponse)
async def process_pdf_endpoint(file: UploadFile = File(...)):
    """
    Handles PDF file uploads, saves the file, and processes it to extract text and metadata.
    Also provides a suggested curl command for the next step (embedding generation).
    """
    try:
        # Validate file type to ensure it's a PDF.
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are accepted")
        
        # Create 'pdfs' directory if it doesn't exist to store uploaded PDFs.
        os.makedirs("pdfs", exist_ok=True)
        
        # Save uploaded file to the 'pdfs' directory.
        file_path = os.path.join("pdfs", file.filename)
        with open(file_path, "wb") as buffer:
            content = await file.read() # Read file content asynchronously.
            buffer.write(content)
        
        # Process the PDF using the document_processor module.
        result = process_pdf(file_path) # This returns a dict with "output_file"
        
        output_json_path = result["output_file"] # e.g., "processed_data/filename.json"
        output_json_filename = os.path.basename(output_json_path) # e.g., "filename.json"
        
        # URL-encode the filename for the next command
        url_encoded_filename = urllib.parse.quote(output_json_filename)
        
        # Construct the next command
        # Assuming the server is running on localhost:8000
        next_command = f"curl -X POST http://localhost:8000/generate-embeddings/{url_encoded_filename}"
        
        return ProcessingResponse(
            success=True,
            output_file=output_json_path,
            metadata=result.get("metadata", {}), # Use .get for safety
            message=f"Successfully processed PDF and saved to {output_json_path}",
            next_embedding_command=next_command
        )
        
    except Exception as e:
        # Catch any exceptions and return a 500 error.
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to generate embeddings for a processed JSON file.
@app.post("/generate-embeddings/{json_file}", response_model=EmbeddingResponse)
async def generate_embeddings_endpoint(json_file: str):
    """
    Generates embeddings for the text chunks in a given JSON file (previously processed from a PDF).
    The JSON file is expected to be in the 'processed_data' directory.
    """
    try:
        # URL-decode the filename to handle spaces and other special characters.
        decoded_json_file = urllib.parse.unquote(json_file)

        # Construct the full path to the JSON file using the decoded name.
        json_path = os.path.join("processed_data", decoded_json_file)
        
        # Check if the JSON file exists.
        if not os.path.exists(json_path):
            raise HTTPException(status_code=404, detail=f"File not found: {decoded_json_file}")
            
        # Generate embeddings using the embedding_pipeline module.
        result = process_json_for_embeddings(json_path)
        
        return EmbeddingResponse(
            success=True,
            input_file=result["input_file"],
            output_file=result["output_file"],
            num_embeddings=result["num_embeddings"],
            embedding_dimension=result["embedding_dimension"],
            message=result["message"]
        )
        
    except Exception as e:
        # Catch any exceptions and return a 500 error.
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to perform a semantic search based on a query.
@app.post("/search")
async def search_endpoint(query: SearchQuery):
    """
    Performs a semantic search using the query provided in the request body.
    It generates an embedding for the query and searches for similar text chunks in ChromaDB.
    """
    try:
        # Generate embedding for the user's query.
        query_embedding = get_embedding_for_query(query.query)
        
        # Search for similar chunks in ChromaDB.
        results = search_similar(query_embedding, query.top_k)
        
        # Format results into a human-readable string.
        output_lines = []
        output_lines.append(f"Query: \"{query.query}\"")
        output_lines.append(f"Found {len(results)} results:")
        
        if results:
            for i, result in enumerate(results):
                output_lines.append(f"--- Result {i+1} ---")
                # Handle newlines in text content for better readability.
                text_content = str(result.get('text', 'N/A')).replace('\n', '\n  ')
                output_lines.append(f"  Text: {text_content}")
                similarity_score = result.get('similarity')
                if similarity_score is not None:
                    output_lines.append(f"  Similarity: {similarity_score:.4f}")
                else:
                    output_lines.append(f"  Similarity: N/A") # Should ideally always have a score
                output_lines.append(f"  Metadata: {result.get('metadata', {})}")
                output_lines.append("-" * 20)
        else:
            output_lines.append("No results found.")
        
        # Return the formatted results as a plain text response.
        return PlainTextResponse("\n".join(output_lines))
        
    except Exception as e:
        # Catch any exceptions and return a 500 error.
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint to verify the server is running.
@app.get("/health")
async def health_check():
    """
    A simple health check endpoint that returns the server status.
    """
    return {"status": "healthy", "version": "1.0.0"}

# Entry point for running the FastAPI application with Uvicorn.
if __name__ == "__main__":
    import uvicorn
    # Runs the FastAPI app on host 0.0.0.0 (accessible externally) and port 8000.
    uvicorn.run(app, host="0.0.0.0", port=8000)

#
#