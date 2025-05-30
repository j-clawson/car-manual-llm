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
    const fileInput = document.getElementById('fileUploadInput');
    
    // Get references to the new image description section elements
    const imageDescriptionSection = document.getElementById('imageDescriptionSection');
    const imageToDescribeName = document.getElementById('imageToDescribeName');
    const imagePromptInput = document.getElementById('imagePromptInput');
    const submitImageDescriptionButton = document.getElementById('submitImageDescriptionButton');
    const uploadedImagePreview = document.getElementById('uploadedImagePreview'); // New image preview element
    
    // Get references to DOM elements for the search functionality
    const searchButton = document.getElementById('searchButton');
    const queryInput = document.getElementById('queryInput');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const resultsSection = document.getElementById('resultsSection');
    const resultsContainer = document.getElementById('resultsContainer');
    const answerText = document.getElementById('answerText');
    
    // Moved Helper Functions Upwards (showToast, handleUploadError, showImageDescriptionPrompt, scrollToQuerySection)
    function showToast(message, type = 'progress') {
        const toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            console.error('Toast container not found!');
            alert(`${type}: ${message}`); // Fallback to alert
            return;
        }
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        const icon = document.createElement('i');
        switch(type) {
            case 'success': icon.className = 'fas fa-check'; break;
            case 'error': icon.className = 'fas fa-exclamation-triangle'; break;
            case 'progress': icon.className = 'fas fa-circle-notch fa-spin'; break;
        }
        const text = document.createElement('span');
        text.textContent = message;
        toast.appendChild(icon);
        toast.appendChild(text);
        toastContainer.appendChild(toast);
        setTimeout(() => toast.classList.add('show'), 10);
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }

    function handleUploadError(error, stage = 'operation') {
        let errorMessage = `Unknown error during ${stage}`;
        // Check for the specific upload file changed error string
        if (error instanceof Error) {
            if (error.message && error.message.includes('UPLOAD_FILE_CHANGED')) {
                errorMessage = `Upload failed: The selected file was changed or moved. Please select the file again and retry.`;
            } else {
                errorMessage = error.message;
            }
        } else if (typeof error === 'string') {
            errorMessage = error;
        }

        showToast(errorMessage, 'error');
        
        // Reset UI elements related to image description if they exist
        if(imageDescriptionSection) imageDescriptionSection.style.display = 'none';
        if(uploadedImagePreview) {
            uploadedImagePreview.style.display = 'none';
            uploadedImagePreview.src = '';
        }
        // Optionally, reset the file input itself to encourage re-selection
        if (fileInput) {
            fileInput.value = ''; // This clears the selected file
        }
        if (fileNameDisplay) {
            fileNameDisplay.textContent = 'No file selected';
            fileNameDisplay.classList.remove('file-selected');
        }
    }

    function showImageDescriptionPrompt(imageUuid, originalImageFilename, imagePath) {
        const existingDynamicButton = document.getElementById('dynamicDescribeButton');
        if (existingDynamicButton) {
            existingDynamicButton.remove();
        }

        if (imageDescriptionSection && imageToDescribeName && imagePromptInput && uploadedImagePreview) {
            imageToDescribeName.textContent = originalImageFilename;
            imagePromptInput.value = sessionStorage.getItem('defaultImagePrompt') || "Describe any car dashboard warning lights or symbols in this image and explain their meaning.";
            
            if (imagePath) {
                uploadedImagePreview.src = imagePath;
                uploadedImagePreview.style.display = 'block';
            } else {
                uploadedImagePreview.style.display = 'none';
                uploadedImagePreview.src = '';
            }
            
            imageDescriptionSection.style.display = 'block';
            imageDescriptionSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        } else {
            console.error('Image description DOM elements not found.');
        }
    }

    function scrollToQuerySection() {
        if (queryInput) {
            queryInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }

    // Update file name display on selection
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            if (fileInput.files && fileInput.files.length > 0) {
                const name = fileInput.files[0].name;
                fileNameDisplay.textContent = name;
                fileNameDisplay.title = name;
                fileNameDisplay.classList.add('file-selected');
            } else {
                fileNameDisplay.textContent = 'No file selected';
                fileNameDisplay.title = '';
                fileNameDisplay.classList.remove('file-selected');
            }
        });
    }

    // Handles file upload (PDF or Image)
    if (uploadForm) {
        uploadForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            let file = fileInput.files && fileInput.files.length > 0 ? fileInput.files[0] : null;

            if (!file) {
                showToast('Please select a PDF or Image file', 'error');
                return;
            }

            const formData = new FormData();
            formData.append('file', file);
            const fName = file.name.toLowerCase();
            const isPdf = fName.endsWith('.pdf');
            const isImage = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'].some(ext => fName.endsWith(ext));

            if (isPdf) {
                showToast('Uploading and processing PDF...', 'progress');
                try {
                    console.log('Attempting to upload PDF:', file);
                    console.log('FormData for PDF:', formData.get('file')); // Check what FormData holds
                    const response = await fetch(`${apiUrl}/process-pdf`, {
                        method: 'POST',
                        body: formData
                    });
                    const result = await response.json();
                    if (!response.ok) throw new Error(result.detail || `HTTP error! status: ${response.status}`);

                    if (result.success) {
                        let jsonFile = '';
                        const parts = result.output_file.split('/');
                        if (parts.length > 0) jsonFile = parts[parts.length - 1];
                        
                        showToast('PDF processed! Generating embeddings...', 'progress');
                        
                        const embedResponse = await fetch(`${apiUrl}/generate-embeddings/${encodeURIComponent(jsonFile)}`, {
                            method: 'POST'
                        });
                        const embedResult = await embedResponse.json();
                        if (!embedResponse.ok) throw new Error(embedResult.detail || `HTTP error! status: ${embedResponse.status}`);

                        if (embedResult.success) {
                            showToast(`PDF processed and indexed! Embeddings: ${embedResult.num_embeddings}. You can now ask questions.`, 'success');
                            scrollToQuerySection();
                        } else {
                            showToast(embedResult.message || 'Error generating PDF embeddings', 'error');
                        }
                    } else {
                        showToast(result.message || 'Error processing PDF', 'error');
                    }
                } catch (error) {
                    handleUploadError(error, 'PDF processing');
                }
            } else if (isImage) {
                showToast('Uploading image...', 'progress');
                try {
                    const response = await fetch(`${apiUrl}/upload-image`, {
                        method: 'POST',
                        body: formData
                    });
                    const result = await response.json();
                    if (!response.ok) throw new Error(result.detail || `HTTP error! status: ${response.status}`);

                    if (result.success && result.filename) {
                        showToast(`Image '${result.original_filename}' uploaded. Describe it next.`, 'success');
                        sessionStorage.setItem('lastUploadedImageUuid', result.filename);
                        sessionStorage.setItem('lastUploadedImageOriginalName', result.original_filename);
                        sessionStorage.setItem('lastUploadedImagePath', result.file_path);
                        sessionStorage.setItem('defaultImagePrompt', "Describe any car dashboard warning lights or symbols in this image and explain their meaning.");
                        showImageDescriptionPrompt(result.filename, result.original_filename, result.file_path);
                        if (queryInput) queryInput.value = ''; // Clear PDF query input
                    } else {
                        showToast(result.message || 'Error uploading image or filename missing.', 'error');
                    }
                } catch (error) {
                    handleUploadError(error, 'Image upload');
                }
            } else {
                showToast('Unsupported file. Select PDF or image (png, jpg, etc.).', 'error');
            }
        });
    }

    // Event listener for the new integrated "Get Description" button
    if (submitImageDescriptionButton) {
        submitImageDescriptionButton.addEventListener('click', async () => {
            const imageFileUuid = sessionStorage.getItem('lastUploadedImageUuid');
            const originalImageName = sessionStorage.getItem('lastUploadedImageOriginalName');
            const userGivenPrompt = imagePromptInput.value.trim();

            if (!imageFileUuid) {
                showToast('No image selected or filename lost. Please re-upload.', 'error');
                if(imageDescriptionSection) imageDescriptionSection.style.display = 'none';
                if(uploadedImagePreview) {
                    uploadedImagePreview.style.display = 'none'; 
                    uploadedImagePreview.src = '';
                }
                return;
            }
            if (!userGivenPrompt) {
                showToast('Please enter a prompt for the image description.', 'error');
                imagePromptInput.focus();
                return;
            }

            showToast(`Requesting description for ${originalImageName || imageFileUuid}...`, 'progress');
            loadingIndicator.style.display = 'block'; // Show main search loading
            resultsSection.style.display = 'none';
            if(imageDescriptionSection) imageDescriptionSection.style.display = 'none'; // Hide prompt section
            if(uploadedImagePreview) {
                uploadedImagePreview.style.display = 'none'; // Hide preview after submit
                uploadedImagePreview.src = ''; // Clear src
            }

            try {
                const describeResponse = await fetch(`${apiUrl}/describe-image/${encodeURIComponent(imageFileUuid)}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ prompt: userGivenPrompt })
                });
                const describeResult = await describeResponse.json();
                loadingIndicator.style.display = 'none';

                if (describeResult.success) {
                    showToast(`Description received for ${originalImageName || describeResult.filename}.`, 'success');
                    answerText.textContent = describeResult.description;
                    resultsContainer.innerHTML = `<p><strong>Prompt used:</strong> ${describeResult.prompt}</p>`; 
                    if (describeResult.matched_symbol_info) {
                        resultsContainer.innerHTML += `<p><strong>Matched Symbol:</strong> ${describeResult.matched_symbol_info.name}</p>`;
                        resultsContainer.innerHTML += `<p><strong>Symbol Meaning:</strong> ${describeResult.matched_symbol_info.meaning}</p>`;
                    }
                    resultsSection.style.opacity = '0';
                    resultsSection.style.display = 'block';
                    setTimeout(() => {
                        resultsSection.style.transition = 'opacity 0.3s ease';
                        resultsSection.style.opacity = '1';
                        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                    }, 10);
                } else {
                    showToast(describeResult.error || 'Failed to get image description.', 'error');
                }
            } catch (error) {
                loadingIndicator.style.display = 'none';
                handleUploadError(error);
            }
        });
    }

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
            
            if (!response.ok) {
                const errorResult = await response.json().catch(() => ({ detail: "Failed to parse error response from server." }));
                throw new Error(errorResult.detail || `Search failed with status: ${response.status}`);
            }

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