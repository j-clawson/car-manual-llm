/**
 * Main application script for Car Manual Assistant
 * Compiled from TypeScript
 */
document.addEventListener('DOMContentLoaded', function() {
    // API endpoint URL - can be changed if hosting elsewhere
    const apiUrl = 'http://localhost:8000';
    
    // Declare selectedFiles variable
    let selectedFiles = [];
    
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
    
    // Add UI elements for PDF processing results
    const pdfProcessingOutput = document.createElement('div');
    pdfProcessingOutput.id = 'pdfProcessingOutput';
    pdfProcessingOutput.className = 'pdf-processing-output';
    document.querySelector('.upload-section').appendChild(pdfProcessingOutput);

    const pdfResultsList = document.createElement('ul');
    pdfResultsList.id = 'pdfResultsList';
    pdfProcessingOutput.appendChild(pdfResultsList);

    const pdfOverallMessage = document.createElement('p');
    pdfOverallMessage.id = 'pdfOverallMessage';
    pdfProcessingOutput.appendChild(pdfOverallMessage);

    const pdfNextSteps = document.createElement('p');
    pdfNextSteps.id = 'pdfNextSteps';
    pdfProcessingOutput.appendChild(pdfNextSteps);
    
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
            // Remove or hide the filename display
            if (imageToDescribeName) {
                imageToDescribeName.style.display = 'none';
            }
            
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
                selectedFiles = Array.from(fileInput.files); // Store the actual File objects
                // Display all selected filenames or a summary
                if (selectedFiles.length === 1) {
                    const name = selectedFiles[0].name;
                    fileNameDisplay.textContent = name;
                    fileNameDisplay.title = name;
                } else {
                    fileNameDisplay.textContent = `${selectedFiles.length} files selected`;
                    fileNameDisplay.title = selectedFiles.map(f => f.name).join(', ');
                }
                fileNameDisplay.classList.add('file-selected');
                
                // Hide results section when new file is selected
                resultsSection.style.display = 'none';
                
                // Hide both sections initially
                const querySection = document.querySelector('.query-section');
                const imageDescriptionSection = document.getElementById('imageDescriptionSection');
                if (querySection) querySection.style.display = 'none';
                if (imageDescriptionSection) imageDescriptionSection.style.display = 'none';
            } else {
                selectedFiles = []; // Clear stored files
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
            
            if (!selectedFiles || selectedFiles.length === 0) {
                showToast('Please select one or more files.', 'error');
                return;
            }

            const allFiles = selectedFiles;
            const pdfFiles = allFiles.filter(file => file.name.toLowerCase().endsWith('.pdf'));
            const imageFiles = allFiles.filter(file => ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'].some(ext => file.name.toLowerCase().endsWith(ext)));

            // Reset UI elements
            pdfProcessingOutput.style.display = 'none';
            pdfResultsList.innerHTML = '';
            pdfOverallMessage.textContent = '';
            pdfNextSteps.textContent = '';
            if(imageDescriptionSection) imageDescriptionSection.style.display = 'none';
            if(uploadedImagePreview) uploadedImagePreview.style.display = 'none';
            const querySection = document.querySelector('.query-section');
            if (querySection) querySection.style.display = 'none';
            resultsSection.style.display = 'none';

            if (pdfFiles.length > 0) {
                showToast(`Processing ${pdfFiles.length} PDF(s)...`, 'progress');
                const formData = new FormData();
                pdfFiles.forEach(file => {
                    formData.append('files', file);
                });

                try {
                    const response = await fetch(`${apiUrl}/process-pdf`, {
                        method: 'POST',
                        body: formData
                    });
                    const result = await response.json();
                    if (!response.ok) throw new Error(result.detail || `HTTP error! status: ${response.status}`);

                    if (result.success) {
                        let allEmbeddingsSuccessful = true;
                        let successfulEmbeddingCount = 0;
                        let totalSuccessfullyProcessed = 0;

                        // Show simplified processing results
                        pdfProcessingOutput.style.display = 'none'; // Hide the detailed output
                        pdfResultsList.innerHTML = '';
                        result.results.forEach(pdfResult => {
                            if (pdfResult.success) {
                                showToast(`Processing ${pdfResult.original_filename}...`, 'progress');
                            }
                        });

                        // Process embeddings for successful PDFs
                        if (result.results && result.results.length > 0) {
                            totalSuccessfullyProcessed = result.results.filter(r => r.success).length;

                            for (const pdfResult of result.results) {
                                if (pdfResult.success && pdfResult.output_file) {
                                    try {
                                        const jsonFile = pdfResult.output_file.split('/').pop();
                                        const embedResponse = await fetch(`${apiUrl}/generate-embeddings/${encodeURIComponent(jsonFile)}`, {
                                            method: 'POST'
                                        });
                                        const embedResult = await embedResponse.json();
                                        if (!embedResponse.ok || !embedResult.success) {
                                            allEmbeddingsSuccessful = false;
                                        } else {
                                            successfulEmbeddingCount++;
                                        }
                                    } catch (embedError) {
                                        allEmbeddingsSuccessful = false;
                                    }
                                }
                            }
                        }

                        if (successfulEmbeddingCount > 0 && successfulEmbeddingCount === totalSuccessfullyProcessed) {
                            showToast(`Successfully processed ${successfulEmbeddingCount} PDF(s). You can now ask questions.`, 'success');
                            if (querySection) {
                                querySection.style.display = 'block';
                                querySection.style.opacity = '0';
                                setTimeout(() => {
                                    querySection.style.transition = 'opacity 0.3s ease';
                                    querySection.style.opacity = '1';
                                    querySection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                                }, 10);
                            }
                            scrollToQuerySection();
                        } else if (successfulEmbeddingCount > 0) {
                            showToast(`${successfulEmbeddingCount} out of ${totalSuccessfullyProcessed} PDFs processed successfully.`, 'warning');
                            if (querySection) querySection.style.display = 'block';
                            scrollToQuerySection();
                        } else {
                            showToast("No PDFs were successfully processed. Please try again.", "error");
                        }
                    } else {
                        showToast(result.message || 'Error processing PDFs', 'error');
                    }
                } catch (error) {
                    handleUploadError(error, 'PDF processing');
                }
            } else if (imageFiles.length === 1) {
                showToast('Uploading image...', 'progress');
                const formData = new FormData();
                formData.append('file', imageFiles[0]);
                
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
            } else if (imageFiles.length > 1) {
                showToast('Please upload only one image at a time.', 'error');
            } else {
                showToast('Unsupported file type(s). Please select PDF(s) or a single image file.', 'error');
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
            
            // Keep image description section visible and show loading state
            if(imageDescriptionSection) {
                imageDescriptionSection.classList.add('loading-state');
                submitImageDescriptionButton.disabled = true;
                submitImageDescriptionButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Getting Description...';
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

                // Reset image description section state
                if(imageDescriptionSection) {
                    imageDescriptionSection.classList.remove('loading-state');
                    submitImageDescriptionButton.disabled = false;
                    submitImageDescriptionButton.innerHTML = '<i class="fas fa-comment-dots"></i> Get Description';
                }

                if (describeResult.success) {
                    showToast(`Description received for ${originalImageName || describeResult.filename}.`, 'success');
                    answerText.textContent = describeResult.description;
                    
                    // For image descriptions, only show the answer without passages
                    if (resultsContainer) {
                        resultsContainer.innerHTML = '';
                    }
                    if (describeResult.matched_symbol_info) {
                        resultsContainer.innerHTML += `<p><strong>Matched Symbol:</strong> ${describeResult.matched_symbol_info.name}</p>`;
                        resultsContainer.innerHTML += `<p><strong>Symbol Meaning:</strong> ${describeResult.matched_symbol_info.meaning}</p>`;
                    }
                    
                    // Hide passages section for image descriptions
                    const passagesSection = document.getElementById('passagesSection');
                    if (passagesSection) passagesSection.style.display = 'none';
                    
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
                // Reset image description section state on error
                if(imageDescriptionSection) {
                    imageDescriptionSection.classList.remove('loading-state');
                    submitImageDescriptionButton.disabled = false;
                    submitImageDescriptionButton.innerHTML = '<i class="fas fa-comment-dots"></i> Get Description';
                }
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
        
        // Show loading state in query section
        const querySection = document.querySelector('.query-section');
        querySection.classList.add('loading-state');
        searchButton.disabled = true;
        searchButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Searching...';
        queryInput.disabled = true;
        
        // Hide previous results
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
            
            // Reset loading state
            querySection.classList.remove('loading-state');
            searchButton.disabled = false;
            searchButton.innerHTML = '<i class="fas fa-search"></i> Search';
            queryInput.disabled = false;
            
            // Display the AI-generated answer
            answerText.textContent = result.answer;
            
            // Clear any previous search results
            if (resultsContainer) {
                resultsContainer.innerHTML = '';
            }
            
            // Show passages section for PDF search results
            const passagesSection = document.getElementById('passagesSection');
            if (passagesSection) passagesSection.style.display = 'none';
            
            // Do NOT render any passages
            // result.results.forEach((item, index) => {
            //     const resultItem = document.createElement('div');
            //     resultItem.className = 'result-item';
            //     // ... code to fill in passage text ...
            //     resultsContainer.appendChild(resultItem);
            // });
            
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
            // Reset loading state on error
            querySection.classList.remove('loading-state');
            searchButton.disabled = false;
            searchButton.innerHTML = '<i class="fas fa-search"></i> Search';
            queryInput.disabled = false;
            
            // Handle any errors that occurred during search
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