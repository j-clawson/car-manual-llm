# Car Manual Assistant
created by James Clawson, Christian Chen, Aryan Gupta and Parnika Chaturvedi @ DataRes UCLA

A Docker-based application that processes car manuals (PDFs) and answers questions about them using AI. The application also supports analyzing car dashboard images for symbol identification.

## Prerequisites

- Docker Desktop installed
- OpenAI API key (get one from [OpenAI Platform](https://platform.openai.com/api-keys))

## Setup Instructions

1. Clone this repository:
   ```bash
   git clone <your-repo-url>
   cd CarManual-LLM
   ```

2. Create a `.env` file in the project root with your OpenAI API key:
   ```bash
   OPENAI_API_KEY=your_openai_api_key_here
   ```

3. Build the Docker image:
   ```bash
   docker build -t car-manual-app:v1 .
   ```

4. Run the container:
   ```bash
   docker run -d \
     -p 8000:8000 \
     -v "$(pwd)/pdfs:/app/pdfs" \
     -v "$(pwd)/processed_data:/app/processed_data" \
     -v "$(pwd)/uploaded_images:/app/uploaded_images" \
     --env-file .env \
     --name car-manual \
     car-manual-app:v1
   ```

5. Access the application at [http://localhost:8000](http://localhost:8000)

## Usage

1. Upload your car manual PDFs using the upload button
2. Wait for the processing to complete
3. Ask questions about your car manual in natural language
4. For dashboard symbols, upload an image and get AI-powered analysis

## Features

- PDF Processing and Question Answering
- Car Dashboard Symbol Recognition
- Interactive Web Interface
- Persistent Storage for Processed Data

## Important Notes

- Keep your OpenAI API key private and never commit it to version control
- The application requires sufficient disk space for PDF processing
- Processed data is stored locally in mounted volumes

## Troubleshooting

If you encounter any issues:

1. Check if Docker is running
2. Verify your OpenAI API key is valid
3. Ensure all required directories exist
4. Check container logs:
   ```bash
   docker logs car-manual
   ```

## Container Management

Stop the container:
```bash
docker stop car-manual
```

Start an existing container:
```bash
docker start car-manual
```

Remove the container:
```bash
docker rm car-manual
```

## Security Considerations

- Never share your `.env` file or API key
- The application stores processed data locally in mounted volumes
- Use appropriate file permissions for mounted volumes

## License

[Your License Here]

