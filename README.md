# Car Manual RAG System

A RAG (Retrieval-Augmented Generation) system for car manuals using FastAPI, ChromaDB, and OpenAI embeddings.

## Features

- PDF processing and chunking (word count based)
- Embedding generation using OpenAI's `text-embedding-3-small` model
- Vector storage using ChromaDB (local, persistent storage in `chroma_db/`)
- FastAPI server for document processing and querying
- Efficient similarity search

## Setup

1.  **Clone the Repository**
    ```bash
    git clone <your-repo-url>
    cd CarManual-LLM 
    ```

2.  **Environment (Conda Recommended)**
    This project is configured to run using a Conda environment. It's recommended to use your Conda `(base)` environment or create a dedicated Conda environment (e.g., `conda create -n carmanual_env python=3.9 && conda activate carmanual_env`).

3.  **Install Dependencies**
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

5.  **Run the FastAPI Server**
    From your project root, with your Conda environment active:
    ```bash
    python -m uvicorn main:app --reload
    ```
    The server will be available at `http://localhost:8000`. If this command fails with "Address already in use," it means port 8000 is occupied. You can find the process using the port with `lsof -i :8000` and stop it using `kill <PID>` (replace `<PID>` with the Process ID found).

## Usage (API Endpoints)

To ingest a PDF and make its content searchable, you'll typically follow a two-step process using the API endpoints:

1.  **Process a PDF (`/process-pdf`)**
    Upload your PDF file to this endpoint. It processes the PDF into text chunks, saves the original PDF to the `pdfs/` directory, and saves the processed chunk data as a JSON file in the `processed_data/` directory.

    Example using `curl` (replace `QUICK REFERENCE GUIDE-cameryAWD.pdf` with your PDF's name):
    ```bash
    curl -X POST -F "file=@manuals/QUICK REFERENCE GUIDE-cameryAWD.pdf" http://localhost:8000/process-pdf
    ```
    The server responds with a JSON object. To make this JSON easier to read in your terminal and to ensure you can see the full `next_embedding_command` without truncation, it's recommended to pipe the output to a JSON pretty-printer like `python -m json.tool` (built-in with Python) or `jq` (if installed). For example:
    ```bash
    curl -X POST -F "file=@manuals/QUICK REFERENCE GUIDE-cameryAWD.pdf" http://localhost:8000/process-pdf | python -m json.tool
    # Or, if you have jq installed:
    # curl -X POST -F "file=@manuals/QUICK REFERENCE GUIDE-cameryAWD.pdf" http://localhost:8000/process-pdf | jq
    ```
    The pretty-printed output will look something like this:
    ```json
    {
      "success": true,
      "output_file": "processed_data/QUICK REFERENCE GUIDE-cameryAWD_20231027_143500.json",
      "metadata": {},
      "message": "Successfully processed PDF and saved to processed_data/QUICK REFERENCE GUIDE-cameryAWD_20231027_143500.json",
      "next_embedding_command": "curl -X POST http://localhost:8000/generate-embeddings/QUICK%20REFERENCE%20GUIDE-cameryAWD_20231027_143500.json"
    }
    ```
    **Carefully copy the entire command string from the `"next_embedding_command"` field.**

2.  **Generate Embeddings (`/generate-embeddings/{json_file}`)**
    Paste the **entire command you copied from the `"next_embedding_command"` field (from Step 1's JSON response)** into your terminal and run it. This command already includes the correctly URL-encoded filename.

    Example (you would paste the actual command you copied):
    ```bash
    # Example of what you would paste from the previous step's output:
    curl -X POST http://localhost:8000/generate-embeddings/QUICK%20REFERENCE%20GUIDE-cameryAWD_20231027_143500.json
    ```
    **Troubleshooting:** If you somehow missed copying the command from Step 1, you can still manually construct it. First, find the latest processed filename using `ls -t processed_data | head -n 1`. Then, URL-encode this filename (replace spaces with `%20`, etc.) and use it in the format: `curl -X POST http://localhost:8000/generate-embeddings/YOUR_URL_ENCODED_FILENAME.json`.

    A successful response will confirm the number of embeddings stored.

3.  **Query the System (`/search`)**
    Once embeddings are generated for at least one document, you can query the system:
    ```bash
    curl -X POST -H "Content-Type: application/json" -d '{"query": "How do I change the oil?", "top_k": 3}' http://localhost:8000/search
    ```
    The results will be returned as formatted plain text.

4.  **Health Check (`/health`)**
    You can check the server's health:
    ```bash
    curl http://localhost:8000/health
    ```

## Testing Queries with `test_queries.py` (Optional)

For a more direct way to test queries against ChromaDB (if embeddings have already been generated via the API), without needing the FastAPI server to be running:

1.  **Modify the Script:**
    Open `test_queries.py` and change the `sample_query` variable.
    ```python
    # In test_queries.py
    sample_query = "Your new question here?"
    number_of_results = 3 
    ```

2.  **Run the Script:**
    Execute it from your project's root directory (with your Conda environment active):
    ```bash
    python test_queries.py
    ```
    The script will output the search results directly to your console.

## Project Structure

- `main.py`: FastAPI application and endpoints.
- `document_processor.py`: PDF processing and word-count based chunking logic.
- `embedding_pipeline.py`: Coordinates processing JSON data to generate and store embeddings.
- `chroma_store.py`: Handles all interactions with ChromaDB (initialization, storage, querying).
- `storage_utils.py`: Utility functions, currently includes `save_chunks_to_json`.
- `embeddings.py`: Generates embeddings using OpenAI models.
- `test_queries.py`: Script for direct command-line query testing against ChromaDB.
- `manuals/`: Place your original PDF manuals here for easy access with `curl`.
- `pdfs/`: Uploaded PDFs are stored here by the `/process-pdf` endpoint.
- `processed_data/`: JSON files containing text chunks from PDFs are stored here.
- `embedded_data/`: Marker JSON files are stored here after embeddings are generated and stored in ChromaDB.
- `chroma_db/`: Persistent storage for the ChromaDB vector database.
- `requirements.txt`: Python package dependencies.
- `.env` (optional): For storing your `OPENAI_API_KEY`.

## Technical Details

- Uses ChromaDB for efficient vector storage and retrieval.
- Vectors are stored locally and persistently in the `chroma_db/` directory.
- PDF text is chunked based on word counts with overlap.
- Uses cosine similarity for vector matching by default in ChromaDB.

