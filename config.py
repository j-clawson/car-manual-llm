# config.py

# --- General Application Settings ---
APP_TITLE = "Car Manual RAG System"
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 8000

# --- Directories ---
PDF_UPLOAD_DIR = "pdfs"
PROCESSED_DATA_DIR = "processed_data"
UPLOADED_IMAGES_DIR = "uploaded_images"
STATIC_DIR = "static"
LOG_DIR = "logs" # For future structured logging

# --- ChromaDB Settings ---
# Collection names
TEXT_EMBEDDINGS_COLLECTION = "car-manuals"
DASHBOARD_SYMBOLS_TEXT_COLLECTION = "dashboard_symbols"
IMAGE_EMBEDDINGS_COLLECTION = "symbol_image_embeddings"

# --- OpenAI Model Settings ---
FINE_TUNED_MODEL_ID = "ft:gpt-3.5-turbo-0125:ucla:car-llm:BXkG9H4N"
VISION_MODEL_ID = "gpt-4-turbo" # As used in vision_analyzer.py - ensure consistency
# We should also centralize the model ID used in vision_analyzer.py here.

# --- Image Processing ---
ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}
IMAGE_SIMILARITY_THRESHOLD = 0.70 # For matching uploaded images to known symbols

# --- API Behavior ---
DEFAULT_SEARCH_TOP_K = 3

# --- Logging ---
LOG_LEVEL = "INFO" # e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# --- CORS Settings ---
CORS_ALLOW_ORIGINS = ["*"] # Allows all origins in development
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["*"] # Allows all methods
CORS_ALLOW_HEADERS = ["*"] # Allows all headers 