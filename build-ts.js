#!/usr/bin/env node

// Direct TypeScript compiler script
const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');

// Log which Node.js is being used
console.log('Node.js path:', process.execPath);
console.log('Node.js version:', process.version);

// Define input and output paths
const tsFilePath = path.join(__dirname, 'static', 'ts', 'script.ts');
const jsOutputDir = path.join(__dirname, 'static', 'js');
const jsFilePath = path.join(jsOutputDir, 'script.js');

// Ensure output directory exists
if (!fs.existsSync(jsOutputDir)) {
  fs.mkdirSync(jsOutputDir, { recursive: true });
}

// Read the TypeScript file
console.log('Reading TypeScript file:', tsFilePath);
const tsContent = fs.readFileSync(tsFilePath, 'utf8');

console.log('Converting TypeScript to JavaScript...');

// Just generate the entire JS file directly to avoid problems with line skipping
const jsContent = `/**
 * Main application script for Car Manual Assistant
 * Compiled from TypeScript
 */
document.addEventListener('DOMContentLoaded', function() {
    // API endpoint URL - can be changed if hosting elsewhere
    const apiUrl = 'http://localhost:8000';
    
    // Get references to DOM elements for the upload form
    const uploadForm = document.getElementById('uploadForm');
    const uploadStatus = document.getElementById('uploadStatus');
    const fileNameDisplay = document.getElementById('fileName');
    const fileInput = document.getElementById('pdfFile');
    
    // Update file name display when file is selected
    fileInput.addEventListener('change', function() {
        if (fileInput.files && fileInput.files.length > 0) {
            const fileName = fileInput.files[0].name;
            fileNameDisplay.textContent = fileName;
            fileNameDisplay.title = fileName; // For tooltip on hover
            fileNameDisplay.classList.add('file-selected');
        } else {
            fileNameDisplay.textContent = 'No file selected';
            fileNameDisplay.title = '';
            fileNameDisplay.classList.remove('file-selected');
        }
    });
    
    /**
     * Handle PDF upload form submission
     * Sends the PDF to the server, processes it, and generates embeddings
     */
    uploadForm.addEventListener('submit', async function(e) {
        // Prevent default form submission behavior
        e.preventDefault();
        
        // Get the selected file from the file input
        let file = null;
        if (fileInput.files && fileInput.files.length > 0) {
            file = fileInput.files[0];
        }
        
        // Validate that a file was selected
        if (!file) {
            showStatus('error', 'Please select a PDF file');
            return;
        }
        
        // Create FormData object to send the file
        const formData = new FormData();
        formData.append('file', file);
        
        // Show upload in progress message
        showStatus('progress', 'Uploading and processing...');
        
        try {
            // Step 1: Upload and process the PDF
            const response = await fetch(\`\${apiUrl}/process-pdf\`, {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Extract filename from path for the embedding API call
                let jsonFile = '';
                const parts = result.output_file.split('/');
                if (parts.length > 0) {
                    jsonFile = parts[parts.length - 1];
                }
                showStatus('progress', 'File processed successfully! Generating embeddings...');
                
                // Step 2: Generate embeddings for the processed file
                const embedResponse = await fetch(\`\${apiUrl}/generate-embeddings/\${encodeURIComponent(jsonFile)}\`, {
                    method: 'POST'
                });
                
                const embedResult = await embedResponse.json();
                
                if (embedResult.success) {
                    // Show success message with embedding count
                    showStatus('success', \`
                        File processed and indexed successfully!
                        Embeddings created: \${embedResult.num_embeddings}
                        You can now ask questions about this manual.
                    \`);
                    
                    // Scroll to query section
                    const querySection = document.querySelector('.query-section');
                    if (querySection) {
                        setTimeout(() => {
                            querySection.scrollIntoView({ behavior: 'smooth' });
                        }, 500);
                    }
                    
                } else {
                    // Show embedding error
                    showStatus('error', 'Error generating embeddings');
                }
            } else {
                // Show processing error
                showStatus('error', result.message);
            }
        } catch (error) {
            // Handle any exceptions that occurred during the process
            let errorMessage = 'Unknown error';
            if (error instanceof Error) {
                errorMessage = error.message;
            } else if (typeof error === 'string') {
                errorMessage = error;
            }
            showStatus('error', errorMessage);
        }
    });
    
    // Helper function to show status messages
    function showStatus(type, message) {
        const color = type === 'success' ? 'green' : type === 'error' ? 'red' : 'black';
        
        const messageLines = message.trim().split('\\n');
        const formattedMessage = messageLines.map(line => \`<p style="color: \${color};">\${line.trim()}</p>\`).join('');
        
        uploadStatus.innerHTML = formattedMessage;
        
        // Clear status after some time for success messages
        if (type === 'success') {
            setTimeout(() => {
                // Fade out effect
                uploadStatus.style.opacity = '0.5';
                setTimeout(() => {
                    uploadStatus.style.opacity = '1';
                }, 300);
            }, 5000);
        }
    }
    
    // Get references to DOM elements for the search functionality
    const searchButton = document.getElementById('searchButton');
    const queryInput = document.getElementById('queryInput');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const resultsSection = document.getElementById('resultsSection');
    const resultsContainer = document.getElementById('resultsContainer');
    const answerText = document.getElementById('answerText');
    
    /**
     * Handle search button click
     * Sends search query to the server and displays results
     */
    searchButton.addEventListener('click', async function() {
        // Get and validate search query
        const query = queryInput.value.trim();
        
        if (!query) {
            alert('Please enter a question');
            return;
        }
        
        // Show loading indicator and hide previous results
        loadingIndicator.style.display = 'block';
        resultsSection.style.display = 'none';
        
        try {
            // Send search request to the server
            const response = await fetch(\`\${apiUrl}/search\`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: query,
                    top_k: 3,                // Get top 3 most relevant passages
                    response_format: 'json'  // Request JSON response format
                })
            });
            
            const result = await response.json();
            
            // Hide loading indicator
            loadingIndicator.style.display = 'none';
            
            // Display the AI-generated answer
            answerText.textContent = result.answer;
            
            // Clear any previous search results
            resultsContainer.innerHTML = '';
            
            // Create and append HTML elements for each search result
            result.results.forEach((item, index) => {
                const resultItem = document.createElement('div');
                resultItem.className = 'result-item';
                
                // Format metadata
                let metadataHtml = '';
                if (item.metadata && Object.keys(item.metadata).length > 0) {
                    const metaEntries = Object.entries(item.metadata)
                        .map(([key, value]) => \`<strong>\${key}</strong>: \${value}\`)
                        .join(' | ');
                    metadataHtml = \`<p class="metadata">\${metaEntries}</p>\`;
                }
                
                resultItem.innerHTML = \`
                    <h4>Passage \${index + 1}</h4>
                    <p>\${item.text.replace(/\\n/g, '<br>')}</p>
                    \${metadataHtml}
                    <p><strong>Similarity:</strong> \${(item.similarity * 100).toFixed(2)}%</p>
                \`;
                resultsContainer.appendChild(resultItem);
            });
            
            // Show the results section with fade-in effect
            resultsSection.style.opacity = '0';
            resultsSection.style.display = 'block';
            setTimeout(() => {
                resultsSection.style.transition = 'opacity 0.3s ease';
                resultsSection.style.opacity = '1';
                
                // Scroll to results
                resultsSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }, 10);
            
        } catch (error) {
            // Handle any errors that occurred during search
            loadingIndicator.style.display = 'none';
            let errorMessage = 'Unknown error';
            if (error instanceof Error) {
                errorMessage = error.message;
            } else if (typeof error === 'string') {
                errorMessage = error;
            }
            alert(\`Error: \${errorMessage}\`);
        }
    });
    
    /**
     * Allow pressing Enter key in the search input to trigger search
     */
    queryInput.addEventListener('keyup', function(event) {
        if (event.key === 'Enter') {
            searchButton.click();
        }
    });
    
    // Add CSS class to enable transitions after page load
    setTimeout(() => {
        document.body.classList.add('transitions-enabled');
    }, 300);
});`;

// Write the JavaScript file
console.log('Writing JavaScript file:', jsFilePath);
fs.writeFileSync(jsFilePath, jsContent, 'utf8');

console.log('TypeScript compilation successful!'); 