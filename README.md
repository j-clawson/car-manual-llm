# Car Manual RAG System

A RAG (Retrieval-Augmented Generation) system for car manuals using FastAPI, ChromaDB, and OpenAI embeddings with a TypeScript frontend.

## Features

- PDF processing and chunking (word count based)
- Embedding generation using OpenAI's `text-embedding-3-small` model
- Vector storage using ChromaDB (local, persistent storage in `chroma_db/`)
- FastAPI server for document processing and querying
- Efficient similarity search
- Modern TypeScript-based frontend interface
- Real-time search results display

## Setup

### Backend Setup

1.  **Clone the Repository**
    ```bash
    git clone <your-repo-url>
    cd CarManual-LLM 
    ```

2.  **Environment (Conda Recommended)**
    This project is configured to run using a Conda environment. It's recommended to use your Conda `(base)` environment or create a dedicated Conda environment:
    ```bash
    conda create -n carmanual_env python=3.9
    conda activate carmanual_env
    ```

3.  **Install Backend Dependencies**
    Ensure your Conda environment is active. Then, install dependencies from your project root using `pip`:
    ```bash
    python -m pip install -r requirements.txt
    ```

4.  **Set Up Environment Variables**
    The application requires your OpenAI API key. You can either:
    *   Create a `.env` file in the project root with the following content:
        ```
        OPENAI_API_KEY='your_openai_api_key_here'
        ```
        The application uses `python-dotenv` to load this variable automatically if a `.env` file is present.
    *   Or, set the `OPENAI_API_KEY` environment variable directly in your shell.

### Frontend Setup

1.  **Install Node.js Dependencies**
    ```bash
    npm install
    ```

2.  **Build TypeScript Files**
    ```bash
    npm run build
    ```

3.  **Watch for TypeScript Changes (Development)**
    During development, you can watch for TypeScript changes:
    ```bash
    npm run watch
    ```

## Running the Application

### Start the Backend Server

From your project root, with your Conda environment active:
```bash
python -m uvicorn main:app --reload
```
The server will be available at `http://localhost:8000`. 

If this command fails with "Address already in use," you can find the process using the port with:
```bash
lsof -i :8000
```
And stop it using:
```bash
kill <PID>
```

### Access the Frontend

1. After starting the backend server, open your web browser
2. Navigate to `http://localhost:8000`
3. The frontend interface will be served automatically through FastAPI's static file serving

## Usage

### Through the Web Interface

1. Use the upload form to submit PDF files
2. Wait for the processing and embedding generation to complete
3. Use the search interface to query your car manual content
4. View results in a clean, formatted display

### Through API Endpoints

To programmatically interact with the system:

1.  **Process a PDF (`/process-pdf`)**
    ```bash
    curl -X POST -F "file=@manuals/YOUR_MANUAL.pdf" http://localhost:8000/process-pdf | python -m json.tool
    ```

2.  **Generate Embeddings (`/generate-embeddings/{json_file}`)**
    Use the command provided in the response from the previous step:
    ```bash
    curl -X POST http://localhost:8000/generate-embeddings/YOUR_PROCESSED_FILE.json
    ```

3.  **Query the System (`/search`)**
    ```bash
    curl -X POST -H "Content-Type: application/json" -d '{"query": "How do I change the oil?", "top_k": 3}' http://localhost:8000/search
    ```

4.  **Health Check (`/health`)**
    ```bash
    curl http://localhost:8000/health
    ```

## Project Structure

### Backend Components
- `main.py`: FastAPI application and endpoints
- `document_processor.py`: PDF processing and word-count based chunking logic
- `embedding_pipeline.py`: Coordinates processing JSON data to generate and store embeddings
- `chroma_store.py`: Handles all interactions with ChromaDB
- `storage_utils.py`: Utility functions
- `embeddings.py`: Generates embeddings using OpenAI models
- `test_queries.py`: Script for direct command-line query testing

### Frontend Components
- `static/`: Frontend assets directory
  - `index.html`: Main frontend interface
  - `styles.css`: Application styling
  - `ts/`: TypeScript source files
  - `js/`: Compiled JavaScript files
- `build-ts.js`: TypeScript build script
- `watch-ts.js`: TypeScript development watch script

### Data Directories
- `manuals/`: Original PDF manuals storage
- `pdfs/`: Uploaded PDFs storage
- `processed_data/`: Processed JSON chunks
- `embedded_data/`: Embedding marker files
- `chroma_db/`: ChromaDB vector database storage

## Technical Details

- Uses ChromaDB for efficient vector storage and retrieval
- Vectors are stored locally and persistently in the `chroma_db/` directory
- PDF text is chunked based on word counts with overlap
- Uses cosine similarity for vector matching
- Frontend built with TypeScript for type safety
- Real-time search results with dynamic UI updates

