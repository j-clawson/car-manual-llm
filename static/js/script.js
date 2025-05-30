/**
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
            showToast('Please select a PDF file', 'error');
            return;
        }
        
        // Create FormData object to send the file
        const formData = new FormData();
        formData.append('file', file);
        
        // Show upload in progress message
        showToast('Uploading and Processing...', 'progress');
        
        try {
            // Step 1: Upload and process the PDF
            const response = await fetch(`${apiUrl}/process-pdf`, {
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
                
                // Step 2: Generate embeddings for the processed file
                const embedResponse = await fetch(`${apiUrl}/generate-embeddings/${encodeURIComponent(jsonFile)}`, {
                    method: 'POST'
                });
                
                const embedResult = await embedResponse.json();
                
                if (embedResult.success) {
                    // Show success message with embedding count
                    showToast(`File processed! ${embedResult.num_embeddings} embeddings created.`, 'success');
                    uploadStatus.innerHTML = ''; // Clear status message
                    uploadStatus.style.opacity = '1'; // Reset opacity for next message
                    
                    // Scroll to query section
                    const querySection = document.querySelector('.query-section');
                    if (querySection) {
                        setTimeout(() => {
                            querySection.scrollIntoView({ behavior: 'smooth' });
                        }, 500);
                    }
                    
                } else {
                    // Show embedding error
                    showToast('Error generating embeddings', 'error');
                }
            } else {
                // Show processing error
                showToast(result.message, 'error');
            }
        } catch (error) {
            // Handle any exceptions that occurred during the process
            let errorMessage = 'Unknown error';
            if (error instanceof Error) {
                errorMessage = error.message;
            } else if (typeof error === 'string') {
                errorMessage = error;
            }
            showToast(errorMessage, 'error');
        }
    });
    
    // Helper function to show status messages
    function showToast(message, type = 'progress') {
        const toastContainer = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        // Create icon element based on type
        const icon = document.createElement('i');
        switch(type) {
            case 'success':
                icon.className = 'fas fa-check';
                break;
            case 'error':
                icon.className = 'fas fa-exclamation-triangle';
                break;
            case 'progress':
                icon.className = 'fas fa-circle-notch fa-spin';
                break;
        }
        
        // Create text span
        const text = document.createElement('span');
        text.textContent = message;
        
        // Add elements to toast
        toast.appendChild(icon);
        toast.appendChild(text);
        toastContainer.appendChild(toast);

        // Show the toast
        setTimeout(() => toast.classList.add('show'), 10);

        // Remove toast after 4 seconds
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 4000);
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
            const response = await fetch(`${apiUrl}/search`, {
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
                        .map(([key, value]) => `<strong>${key}</strong>: ${value}`)
                        .join(' | ');
                    metadataHtml = `<p class="metadata">${metaEntries}</p>`;
                }
                
                resultItem.innerHTML = `
                    <h4>Passage ${index + 1}</h4>
                    <p>${item.text.replace(/\n/g, '<br>')}</p>
                    ${metadataHtml}
                    <p><strong>Similarity:</strong> ${(item.similarity * 100).toFixed(2)}%</p>
                `;
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
            alert(`Error: ${errorMessage}`);
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

    const placeholderQuestions = [
        "How do I adjust the instrument panel light brightness?",
        "What does the check engine light mean?",
        "How to change the oil filter?",
        "Where is the spare tire located?",
        "How do I reset the maintenance light?"
    ];

    const input = document.getElementById("queryInput");
    let questionIndex = 0;
    let charIndex = 0;
    let typing = true;

    function typePlaceholder() {
        const currentQuestion = placeholderQuestions[questionIndex];

        if (typing) {
            if (charIndex <= currentQuestion.length) {
                input.placeholder = currentQuestion.substring(0, charIndex++);
                setTimeout(typePlaceholder, 80);
            } else {
                typing = false;
                setTimeout(typePlaceholder, 2000); // pause before deleting
            }
        } else {
            if (charIndex > 0) {
                input.placeholder = currentQuestion.substring(0, --charIndex);
                setTimeout(typePlaceholder, 40);
            } else {
                typing = true;
                questionIndex = (questionIndex + 1) % placeholderQuestions.length;
                setTimeout(typePlaceholder, 500);
            }
        }
    }

    typePlaceholder();
});