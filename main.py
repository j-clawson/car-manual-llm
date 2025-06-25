import sys
import multiprocessing
import urllib.parse
import logging
import config
import uuid
import os

# Ensures that multiprocessing works correctly on macOS.
if sys.platform == 'darwin':
    multiprocessing.set_executable(sys.executable)

# Configure logging
logging.basicConfig(level=config.LOG_LEVEL, format=config.LOG_FORMAT)
logger = logging.getLogger(__name__)
if not os.path.exists(config.LOG_DIR):
    os.makedirs(config.LOG_DIR)
file_handler = logging.FileHandler(os.path.join(config.LOG_DIR, 'app.log'))
file_handler.setFormatter(logging.Formatter(config.LOG_FORMAT))
logger.addHandler(file_handler)

# Suppress specific ChromaDB warnings about existing embedding IDs
logging.getLogger('chromadb.segment.impl.vector.local_persistent_hnsw').setLevel(logging.ERROR)
logging.getLogger('chromadb.segment.impl.metadata.sqlite').setLevel(logging.ERROR)

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Path as FastApiPath, Request
from fastapi.responses import JSONResponse, PlainTextResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from document_processor import process_pdf
from embedding_pipeline import process_json_for_embeddings, get_pending_documents
from embeddings import get_embedding_for_query, client as openai_client
from chroma_store import search_similar, get_collection
from typing import List, Optional
from vision_analyzer import get_image_description_from_gpt4v
from image_embedding_utils import get_image_embedding

# Initialize FastAPI application
app = FastAPI(title=config.APP_TITLE)

# Add CORS middleware to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ALLOW_ORIGINS,
    allow_credentials=config.CORS_ALLOW_CREDENTIALS,
    allow_methods=config.CORS_ALLOW_METHODS,
    allow_headers=config.CORS_ALLOW_HEADERS,
)

# Create static directory if it doesn't exist
os.makedirs(config.STATIC_DIR, exist_ok=True)

# Mount the static files directory
app.mount(f"/{config.STATIC_DIR}", StaticFiles(directory=config.STATIC_DIR), name="static")

# Directory for storing uploaded images
os.makedirs(config.UPLOADED_IMAGES_DIR, exist_ok=True)

# Mount the uploaded images directory to be served statically
app.mount(f"/{config.UPLOADED_IMAGES_DIR}", StaticFiles(directory=config.UPLOADED_IMAGES_DIR), name="uploaded_images")

IMAGE_EMBEDDINGS_COLLECTION_NAME = "symbol_image_embeddings"
SIMILARITY_THRESHOLD = 0.70

# Define the fine-tuned model ID
FINE_TUNED_MODEL = "ft:gpt-3.5-turbo-0125:ucla:car-llm:BXkG9H4N"

# Pydantic model for individual PDF processing result
class PDFProcessingResult(BaseModel):
    success: bool
    output_file: str
    metadata: dict
    message: str
    original_filename: str

# Pydantic model for the response of the PDF processing endpoint.
class ProcessingResponse(BaseModel):
    success: bool
    results: List[PDFProcessingResult]
    message: str

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
    top_k: Optional[int] = config.DEFAULT_SEARCH_TOP_K
    response_format: Optional[str] = None

# Pydantic model for image upload response
class ImageUploadResponse(BaseModel):
    success: bool
    filename: str
    original_filename: str
    file_path: str
    message: str
    describe_command: Optional[str] = None

# Pydantic model for image description request body
class ImageDescriptionPrompt(BaseModel):
    prompt: str = "Describe any car dashboard warning lights or symbols in this image and explain their meaning."

# Pydantic model for image description response
class ImageDescriptionResponse(BaseModel):
    success: bool
    filename: str
    prompt: str
    description: str
    error: Optional[str] = None

# Endpoint to process uploaded PDF files.
@app.post("/process-pdf", response_model=ProcessingResponse)
async def process_pdf_endpoint(request: Request, files: List[UploadFile] = File(...)):
    """
    Handles multiple PDF file uploads, saves the files, and processes them to extract text and metadata.
    """
    results = []
    total_files = len(files)
    successful_files = 0

    try:
        # Create 'pdfs' directory if it doesn't exist
        os.makedirs(config.PDF_UPLOAD_DIR, exist_ok=True)
        
        for file in files:
            try:
                # Validate file type
                if not file.filename.lower().endswith('.pdf'):
                    results.append(PDFProcessingResult(
                        success=False,
                        output_file="",
                        metadata={},
                        message="Not a PDF file",
                        original_filename=file.filename
                    ))
                    continue

                # Save uploaded file
                file_path = os.path.join(config.PDF_UPLOAD_DIR, file.filename)
                with open(file_path, "wb") as buffer:
                    content = await file.read()
                    buffer.write(content)
                logger.info(f"PDF file '{file.filename}' saved to '{file_path}'")

                # Process the PDF
                result = process_pdf(file_path)
                successful_files += 1
                
                results.append(PDFProcessingResult(
                    success=True,
                    output_file=result["output_file"],
                    metadata=result.get("metadata", {}),
                    message="Successfully processed",
                    original_filename=file.filename
                ))

            except Exception as e:
                logger.error(f"Error processing PDF '{file.filename}': {e}", exc_info=True)
                results.append(PDFProcessingResult(
                    success=False,
                    output_file="",
                    metadata={},
                    message="Processing failed",
                    original_filename=file.filename
                ))

        overall_success = successful_files > 0
        overall_message = f"Successfully processed {successful_files} out of {total_files} PDF(s)"
        
        return ProcessingResponse(
            success=overall_success,
            results=results,
            message=overall_message
        )

    except Exception as e:
        logger.error(f"Error in bulk PDF processing: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while processing PDFs: {type(e).__name__}")

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
        json_path = os.path.join(config.PROCESSED_DATA_DIR, decoded_json_file)
        
        # Check if the JSON file exists.
        if not os.path.exists(json_path):
            logger.warning(f"Embeddings generation attempt for non-existent JSON file: {json_path}")
            raise HTTPException(status_code=404, detail=f"File not found: {decoded_json_file}")
            
        # Generate embeddings using the embedding_pipeline module.
        logger.info(f"Generating embeddings for JSON file: {json_path}")
        result = process_json_for_embeddings(json_path, collection_name=config.TEXT_EMBEDDINGS_COLLECTION)
        
        return EmbeddingResponse(
            success=True,
            input_file=result["input_file"],
            output_file=result["output_file"],
            num_embeddings=result["num_embeddings"],
            embedding_dimension=result["embedding_dimension"],
            message=result["message"]
        )
        
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        logger.error(f"Error generating embeddings for '{json_file}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while generating embeddings: {type(e).__name__}")

# Endpoint to upload an image file.
@app.post("/upload-image", response_model=ImageUploadResponse)
async def upload_image_endpoint(request: Request, file: UploadFile = File(...)):
    """
    Handles image file uploads, saves the file to a designated directory.
    Provides a suggested curl command for the next step (image description).
    """
    original_filename = file.filename
    file_extension = os.path.splitext(original_filename)[1].lower()
    if file_extension not in config.ALLOWED_IMAGE_EXTENSIONS:
        logger.warning(f"Image upload attempt with invalid extension: {original_filename} ({file_extension})")
        raise HTTPException(status_code=400, detail=f"Only image files with extensions {config.ALLOWED_IMAGE_EXTENSIONS} are accepted")

    try:
        # Generate a unique filename to prevent overwrites and ensure security
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        local_file_path = os.path.join(config.UPLOADED_IMAGES_DIR, unique_filename)
        
        with open(local_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        logger.info(f"Image '{original_filename}' uploaded and saved as '{unique_filename}' to '{local_file_path}'")
        
        # Construct the URL path for the browser
        browser_accessible_file_path = f"/{config.UPLOADED_IMAGES_DIR}/{unique_filename}"

        # URL-encode the unique_filename for the next command
        url_encoded_filename = urllib.parse.quote(unique_filename)
        base_url = str(request.base_url).rstrip('/')
        # Update describe_command to use POST with JSON body
        next_command = f"curl -X POST {base_url}/describe-image/{url_encoded_filename} -H 'Content-Type: application/json' -d '{{\"prompt\": \"Describe this image in detail.\"}}'"

        return ImageUploadResponse(
            success=True,
            filename=unique_filename,
            original_filename=original_filename,
            file_path=browser_accessible_file_path,
            message=f"Successfully uploaded image '{original_filename}' (saved as '{unique_filename}')",
            describe_command=next_command
        )
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        logger.error(f"Could not upload image '{original_filename}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Could not upload image: {type(e).__name__}")

# Endpoint to describe an uploaded image using GPT-4 Vision
@app.post("/describe-image/{image_filename}", response_model=ImageDescriptionResponse)
async def describe_image_endpoint(
    body: ImageDescriptionPrompt,
    image_filename: str = FastApiPath(..., title="Filename of the uploaded image", description="The unique filename of the image previously uploaded via /upload-image.")
):
    """
    Describes an image previously uploaded using GPT-4 Vision.
    Attempts to find a similar known symbol image to provide context to GPT-4V.
    The image_filename must exist in the UPLOADED_IMAGES_DIR.
    A prompt should be provided in the request body as JSON: e.g., {"prompt": "Describe this error."}
    """
    user_prompt = body.prompt
    
    # Sanitize filename from path to prevent traversal (already a UUID, but good practice)
    safe_image_filename = os.path.basename(image_filename)
    image_path = os.path.join(config.UPLOADED_IMAGES_DIR, safe_image_filename)

    if not os.path.exists(image_path):
        logger.warning(f"Describe image attempt for non-existent file: {image_path}")
        raise HTTPException(status_code=404, detail=f"Image file not found: {safe_image_filename}. Please upload it first via /upload-image.")

    augmented_prompt = user_prompt

    try:
        # 1. Get embedding for the uploaded image
        logger.info(f"Generating embedding for uploaded image: {image_path}")
        uploaded_image_embedding = get_image_embedding(image_path)

        if uploaded_image_embedding:
            logger.info(f"Searching for similar known symbol images in '{config.IMAGE_EMBEDDINGS_COLLECTION}'.")
            try:
                similar_images = search_similar(
                    query_embedding=uploaded_image_embedding,
                    collection_name=config.IMAGE_EMBEDDINGS_COLLECTION,
                    top_k=1
                )
                if similar_images and similar_images[0]['similarity'] is not None and similar_images[0]['similarity'] >= config.IMAGE_SIMILARITY_THRESHOLD:
                    matched_symbol = similar_images[0]
                    matched_metadata = matched_symbol.get('metadata', {})
                    matched_symbol_name = matched_metadata.get('symbol_name', 'unknown symbol')
                    original_meaning = matched_metadata.get('original_meaning', 'Meaning not available in image metadata.')
                    
                    logger.info(f"Found a similar known symbol: '{matched_symbol_name}' with similarity: {matched_symbol['similarity']:.4f}")
                    augmentation = f"This uploaded image looks visually similar to our known symbol named '{matched_symbol_name}'. "
                    augmentation += f"This symbol typically means: '{original_meaning}'. "
                    augmented_prompt = augmentation + user_prompt
                else:
                    if similar_images and similar_images[0]['similarity'] is not None:
                        logger.info(f"Closest image match similarity {similar_images[0]['similarity']:.4f} is below threshold {config.IMAGE_SIMILARITY_THRESHOLD}.")
                    else:
                        logger.info("No similar known symbol images found or similarity was None.")
            except Exception as search_ex:
                logger.error(f"Error during image similarity search for '{safe_image_filename}': {search_ex}", exc_info=True)
        else:
            logger.warning(f"Could not generate embedding for uploaded image '{safe_image_filename}'. Proceeding without image similarity context.")

        logger.info(f"Describing image: {image_path} with prompt (potentially augmented): '{augmented_prompt[:200]}...'")
        description = get_image_description_from_gpt4v(image_path_or_url=image_path, prompt=augmented_prompt)
        return ImageDescriptionResponse(
            success=True,
            filename=safe_image_filename,
            prompt=augmented_prompt,
            description=description
        )
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        logger.error(f"Error during image description for '{safe_image_filename}': {type(e).__name__} - {str(e)}", exc_info=True)
        return ImageDescriptionResponse(
            success=False,
            filename=safe_image_filename,
            prompt=user_prompt,
            description="",
            error=f"Failed to get description from vision model: {type(e).__name__}"
        )

# Endpoint to perform a semantic search and generate answer using fine-tuned model
@app.post("/search")
async def search_endpoint(query: SearchQuery, request: Request):
    """
    Performs a semantic search using the query provided in the request body.
    It generates an embedding for the query, searches for similar text chunks in ChromaDB,
    (now potentially searching both text and symbol collections)
    and then uses the fine-tuned model to generate a concise answer.
    """
    try:
        logger.info(f"Received search query: '{query.query}' with top_k={query.top_k}")
        query_embedding = get_embedding_for_query(query.query)
        
        # Search in car manuals collection
        manual_results = search_similar(query_embedding, collection_name=config.TEXT_EMBEDDINGS_COLLECTION, top_k=query.top_k)
        logger.info(f"Manual results for query '{query.query}': {manual_results}")
        
        # Search in dashboard symbols collection
        symbol_results = search_similar(query_embedding, collection_name=config.DASHBOARD_SYMBOLS_TEXT_COLLECTION, top_k=query.top_k)
        logger.info(f"Symbol results for query '{query.query}': {symbol_results}")

        combined_results_dict = {}
        for res_list in [manual_results, symbol_results]:
            for res in res_list:
                # Use text content as the key for deduplication to avoid showing identical passages.
                # Ensure 'text' key exists and is a string.
                text_key = str(res.get('text', '')) # Use str() to handle potential None and ensure string type
                combined_results_dict[text_key] = res 
        
        all_results = sorted(
            [res for res in combined_results_dict.values() if res.get('similarity') is not None],
            key=lambda x: x['similarity'], 
            reverse=True
        )[:query.top_k]
        
        output_lines = []
        output_lines.append(f"Query: \"{query.query}\"")
        output_lines.append(f"Found {len(all_results)} combined results from '{config.TEXT_EMBEDDINGS_COLLECTION}' and '{config.DASHBOARD_SYMBOLS_TEXT_COLLECTION}':")
        
        context = ""
        formatted_results = []
        
        if all_results:
            for i, result in enumerate(all_results):
                text_content = str(result.get('text', 'N/A')).replace('\n', '\n  ')
                similarity_score = result.get('similarity')
                metadata = result.get('metadata', {})
                source_doc_id = metadata.get('source_document_id', 'unknown_source_doc')
                source_collection = metadata.get('collection_source', 'unknown_collection')
                
                # + Format similarity score separately to handle None case correctly in f-string
                similarity_str = f"{similarity_score:.4f}" if similarity_score is not None else "N/A" # +

                output_lines.append(f"--- Result {i+1} (Similarity: {similarity_str}, Source: {source_collection}, Doc ID: {source_doc_id}) ---") # Modified
                output_lines.append(f"  Text: {text_content}")
                output_lines.append(f"  Metadata: {metadata}")
                output_lines.append("-" * 20)
                
                formatted_results.append({
                    "text": text_content,
                    "similarity": similarity_score,
                    "metadata": metadata,
                    "source_collection": source_collection,
                    "source_document_id": source_doc_id
                })
                
                context += text_content + "\n\n"
        else:
            output_lines.append("No results found.")
            logger.info(f"No results found for query: '{query.query}'")
        
        logger.info(f"Context being sent to LLM for query '{query.query}':\n{context}")

        answer = "No relevant information found to answer your query."
        error_message_llm = None
        
        if context:
            try:
                logger.info(f"Sending query to fine-tuned model: {config.FINE_TUNED_MODEL_ID}")
                response = openai_client.chat.completions.create(
                    model=config.FINE_TUNED_MODEL_ID, 
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant specializing in car manuals. Based on the provided context, give a comprehensive and detailed answer to the user\'s question. Explain the steps or information clearly."},
                        {"role": "user", "content": f"Context: {context}\n\nQuestion: {query.query}"}
                    ],
                    temperature=0.3,
                    max_tokens=450
                )
                answer = response.choices[0].message.content
                logger.info(f"Received answer from fine-tuned model for query: '{query.query}'")
                output_lines.append("\nGenerated Answer:")
                output_lines.append(answer)
            except Exception as e_llm:
                error_message_llm = str(e_llm)
                logger.error(f"Error generating answer with fine-tuned model for query '{query.query}': {e_llm}", exc_info=True)
                output_lines.append(f"\nError generating answer with LLM: {error_message_llm}")
        
        # Check if the client wants JSON using request headers or query param
        # For simplicity, sticking to query.response_format for now
        if query.response_format == "json":
            return JSONResponse({
                "query": query.query,
                "answer": answer,
                "results": formatted_results,
                "error_llm": error_message_llm
            })
        else:
            return PlainTextResponse("\n".join(output_lines))
        
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        logger.error(f"Error during search for query '{query.query}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during search: {type(e).__name__}")

# Health check endpoint to verify the server is running.
@app.get("/health")
async def health_check():
    """
    A simple health check endpoint that returns the server status.
    """
    logger.info("Health check requested.")
    return {"status": "healthy", "version": "1.0.0", "app_title": config.APP_TITLE}

# Root endpoint to redirect to our UI
@app.get("/")
async def root():
    logger.info("Root path requested, redirecting to static UI.")
    return RedirectResponse(url=f"/{config.STATIC_DIR}/index.html")

# Entry point for running the FastAPI application with Uvicorn.
if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting Uvicorn server on {config.SERVER_HOST}:{config.SERVER_PORT}")
    uvicorn.run(app, host=config.SERVER_HOST, port=config.SERVER_PORT)

#
#