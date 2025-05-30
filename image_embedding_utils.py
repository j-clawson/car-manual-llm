from sentence_transformers import SentenceTransformer
from PIL import Image
import requests
from io import BytesIO
import os
from typing import List

# Load a pre-trained CLIP model
# You can choose other models from sentence-transformers that are suitable for image embeddings.
# 'clip-ViT-B-32' is a common choice.
IMAGE_EMBEDDING_MODEL = None

def _initialize_model():
    global IMAGE_EMBEDDING_MODEL
    if IMAGE_EMBEDDING_MODEL is None:
        try:
            print("Initializing image embedding model (this may take a moment on first run)...")
            IMAGE_EMBEDDING_MODEL = SentenceTransformer('clip-ViT-B-32')
            print("Image embedding model initialized successfully.")
        except Exception as e:
            print(f"Error initializing SentenceTransformer model: {e}")
            # Potentially re-raise or handle as a critical failure
            raise

def get_image_embedding(image_path_or_url: str) -> List[float]:
    """
    Generates an embedding for a single image using a pre-trained model.
    The image can be a local path or a publicly accessible URL.

    Args:
        image_path_or_url (str): Local path to the image or its public URL.

    Returns:
        List[float]: The embedding vector for the image, or None if an error occurs.
    """
    _initialize_model() # Ensure model is loaded
    if IMAGE_EMBEDDING_MODEL is None:
        print("Image embedding model is not available.")
        return None

    try:
        img_pil = None
        if image_path_or_url.startswith(("http://", "https://")):
            try:
                # Define common browser-like headers
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': 'image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                }
                response = requests.get(image_path_or_url, headers=headers, timeout=15) # Added headers and increased timeout slightly
                response.raise_for_status() # Raise an exception for bad status codes
                img_pil = Image.open(BytesIO(response.content))
                print(f"Successfully loaded image from URL: {image_path_or_url}")
            except requests.exceptions.RequestException as e:
                print(f"Error fetching image from URL {image_path_or_url}: {e}")
                return None
            except IOError as e:
                print(f"Error opening image from URL {image_path_or_url} (possibly invalid image format): {e}")
                return None
        elif os.path.exists(image_path_or_url):
            try:
                img_pil = Image.open(image_path_or_url)
                print(f"Successfully loaded image from local path: {image_path_or_url}")
            except FileNotFoundError:
                print(f"Error: Image file not found at local path: {image_path_or_url}")
                return None
            except IOError as e:
                print(f"Error opening local image {image_path_or_url} (possibly invalid image format or permissions): {e}")
                return None
        else:
            print(f"Error: Image path does not exist and is not a valid URL: {image_path_or_url}")
            return None
        
        if img_pil:
            # Generate embedding
            # The encode method of SentenceTransformer for images typically expects a PIL Image object.
            embedding = IMAGE_EMBEDDING_MODEL.encode(img_pil, convert_to_tensor=False).tolist()
            print(f"Generated embedding for image: {image_path_or_url}")
            return embedding
        else:
            # This case should ideally be caught by earlier checks, but as a fallback:
            print(f"Could not load image for embedding: {image_path_or_url}")
            return None

    except Exception as e:
        print(f"An unexpected error occurred while generating image embedding for {image_path_or_url}: {e}")
        # Depending on the severity, you might want to return None or re-raise
        return None

if __name__ == '__main__':
    print("\n--- Running image_embedding_utils.py example ---")
    
    # Ensure the model downloads on first run if not cached
    _initialize_model()

    # Example 1: Local image (Create a dummy one if it doesn't exist for testing)
    dummy_image_path = "test_dummy_image.png"
    try:
        # Create a small, simple PNG if it doesn't exist
        if not os.path.exists(dummy_image_path):
            from PIL import ImageDraw
            img = Image.new('RGB', (60, 30), color = 'red')
            d = ImageDraw.Draw(img)
            d.text((10,10), "Test", fill=(255,255,0))
            img.save(dummy_image_path)
            print(f"Created dummy image: {dummy_image_path}")
        
        print(f"\nTesting with local image: {dummy_image_path}")
        local_embedding = get_image_embedding(dummy_image_path)
        if local_embedding:
            print(f"Local image embedding (first 5 dims): {local_embedding[:5]}...")
            print(f"Local image embedding dimension: {len(local_embedding)}")
        else:
            print("Failed to get embedding for local image.")

    except Exception as e:
        print(f"Error in local image test: {e}")
    finally:
        # Clean up dummy image
        if os.path.exists(dummy_image_path) and "dummy_image" in dummy_image_path:
             #os.remove(dummy_image_path)
             #print(f"Cleaned up dummy image: {dummy_image_path}")
             pass # Keeping it for now for easier re-testing

    # Example 2: Image from URL
    # Using a known good image URL for testing (e.g., from Wikipedia or a public image host)
    # Make sure this URL points to a direct image, not an HTML page containing an image.
    test_image_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Warning_icon.svg/120px-Warning_icon.svg.png" # A simple warning icon
    print(f"\nTesting with image URL: {test_image_url}")
    try:
        url_embedding = get_image_embedding(test_image_url)
        if url_embedding:
            print(f"URL image embedding (first 5 dims): {url_embedding[:5]}...")
            print(f"URL image embedding dimension: {len(url_embedding)}")
        else:
            print("Failed to get embedding for URL image.")
    except Exception as e:
        print(f"Error in URL image test: {e}")

    print("--- Finished image_embedding_utils.py example ---") 