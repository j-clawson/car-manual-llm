import sys
import multiprocessing
import urllib.parse

# Ensures that multiprocessing works correctly on macOS.
if sys.platform == 'darwin':
    multiprocessing.set_executable(sys.executable)

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse, PlainTextResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
from document_processor import process_pdf
from embedding_pipeline import process_json_for_embeddings, get_pending_documents
from embeddings import get_embedding_for_query, client as openai_client
from chroma_store import search_similar
from typing import List, Optional

# Initialize FastAPI application
app = FastAPI(title="Car Manual RAG System")

# Add CORS middleware to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins in development
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Create static directory if it doesn't exist
os.makedirs("static", exist_ok=True)

# Mount the static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Define the fine-tuned model ID
FINE_TUNED_MODEL = "ft:gpt-3.5-turbo-0125:ucla:car-llm:BXkG9H4N"

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
    response_format: Optional[str] = None # Can be "json" to get JSON response

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

# Endpoint to perform a semantic search and generate answer using fine-tuned model
@app.post("/search")
async def search_endpoint(query: SearchQuery):
    """
    Performs a semantic search using the query provided in the request body.
    It generates an embedding for the query, searches for similar text chunks in ChromaDB,
    and then uses the fine-tuned model to generate a concise answer.
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
        
        # Extract context from search results
        context = ""
        formatted_results = []
        
        if results:
            for i, result in enumerate(results):
                # Handle newlines in text content for better readability.
                text_content = str(result.get('text', 'N/A')).replace('\n', '\n  ')
                similarity_score = result.get('similarity')
                metadata = result.get('metadata', {})
                
                # Format for plain text output
                output_lines.append(f"--- Result {i+1} ---")
                output_lines.append(f"  Text: {text_content}")
                if similarity_score is not None:
                    output_lines.append(f"  Similarity: {similarity_score:.4f}")
                else:
                    output_lines.append(f"  Similarity: N/A")
                output_lines.append(f"  Metadata: {metadata}")
                output_lines.append("-" * 20)
                
                # Store for JSON response
                formatted_results.append({
                    "text": text_content,
                    "similarity": similarity_score,
                    "metadata": metadata
                })
                
                # Add to context for the fine-tuned model
                context += text_content + "\n\n"
        else:
            output_lines.append("No results found.")
        
        # Generate answer using the fine-tuned model
        answer = "No relevant information found to answer your query."
        error_message = None
        
        if context:
            try:
                # Use fine-tuned model to generate a concise answer
                response = openai_client.chat.completions.create(
                    model=FINE_TUNED_MODEL,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant specializing in car manuals. Provide concise and direct answers based on the given context."},
                        {"role": "user", "content": f"Context: {context}\n\nQuestion: {query.query}"}
                    ],
                    temperature=0.2,  # Lower temperature for more focused answers
                    max_tokens=200    # Limit response length for conciseness
                )
                answer = response.choices[0].message.content
                
                # Add the answer to the output
                output_lines.append("\nGenerated Answer:")
                output_lines.append(answer)
            except Exception as e:
                error_message = str(e)
                output_lines.append(f"\nError generating answer: {error_message}")
        
        # Check if the client wants JSON
        accept_header = query.response_format if hasattr(query, 'response_format') else None
        
        if accept_header == "json":
            return JSONResponse({
                "query": query.query,
                "answer": answer,
                "results": formatted_results,
                "error": error_message
            })
        else:
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

# Root endpoint to redirect to our UI
@app.get("/")
async def root():
    return RedirectResponse(url="/static/index.html")

# Entry point for running the FastAPI application with Uvicorn.
if __name__ == "__main__":
    import uvicorn
    # Runs the FastAPI app on host 0.0.0.0 (accessible externally) and port 8000.
    uvicorn.run(app, host="0.0.0.0", port=8000)

#
#