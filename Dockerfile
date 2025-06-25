# Start with Python 3.9 (stable version for ML libraries)
FROM python:3.9-slim

# Set up working directory
WORKDIR /app

# Install only the essential system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user with the same UID as the host user
RUN useradd -m -u 501 appuser

# Copy only the requirements first (better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY main.py .
COPY static/ static/
COPY document_processor.py .
COPY embedding_pipeline.py .
COPY embeddings.py .
COPY chroma_store.py .
COPY storage_utils.py .
COPY config.py .
COPY vision_analyzer.py .
COPY image_embedding_utils.py .

# Create directories for uploaded files and data and set permissions
RUN mkdir -p pdfs processed_data uploaded_images logs && \
    chown -R appuser:appuser /app && \
    chmod -R 775 /app

# Switch to non-root user
USER appuser

# Environment variable for Python to run in production mode
ENV PYTHONUNBUFFERED=1

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"] 