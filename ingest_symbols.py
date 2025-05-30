import csv
import os
# from embedding_pipeline import get_embedding_for_text_chunks # No longer needed directly here
from chroma_store import store_embeddings # We'll need to adapt/confirm this
from embeddings import create_embeddings # Use this for batch embedding
from image_embedding_utils import get_image_embedding # Import for image embeddings

# Define the path to your CSV file
CSV_FILE_PATH = os.path.join("dashboard_symbols", "toyota_dashboard_symbols.csv")
# Define a collection name for symbols in ChromaDB
CHROMA_COLLECTION_NAME = "dashboard_symbols"
IMAGE_EMBEDDINGS_COLLECTION_NAME = "symbol_image_embeddings"


def process_and_embed_symbols():
    """
    Reads symbol data from the CSV, creates combined text for embedding,
    generates embeddings, and stores them in ChromaDB.
    """
    print(f"Starting symbol ingestion from {CSV_FILE_PATH}...")
    symbols_to_embed = []
    all_texts = []
    all_metadata = []

    # For storing image embeddings and their metadata
    all_image_embeddings = []
    all_image_metadata = []
    all_image_ids = [] # Separate IDs for image embeddings, linked to symbol if needed

    if not os.path.exists(CSV_FILE_PATH):
        print(f"Error: CSV file not found at {CSV_FILE_PATH}")
        return

    with open(CSV_FILE_PATH, mode='r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for i, row in enumerate(reader):
            symbol_name = row.get("symbol_name", "").strip()
            image_url = row.get("image_url", "").strip()
            meaning = row.get("meaning", "").strip()

            if not symbol_name or not meaning:
                print(f"Skipping row {i+1} due to missing symbol_name or meaning.")
                continue

            # Combine name and meaning for a richer embedding context
            combined_text = f"Symbol: {symbol_name}. Meaning: {meaning}"
            
            # The ID for ChromaDB should be unique
            # Using image_url as a base for ID, but ensure it's a valid Chroma ID (no special chars, etc.)
            # A safer bet might be a processed symbol_name + index or a UUID
            unique_id = f"symbol_{i}_{symbol_name.replace(' ', '_').lower().replace('(','').replace(')','').replace('.','')}"

            all_texts.append(combined_text)
            all_metadata.append({
                "id": unique_id, # Store the unique ID in metadata as well for reference
                "symbol_name": symbol_name,
                "image_url": image_url,
                "original_meaning": meaning, # Store original meaning separately if needed
                "source": "toyota_dashboard_symbols_csv"
            })

            # Now, attempt to get image embedding for the symbol's image_url
            if image_url:
                print(f"Processing image for symbol '{symbol_name}' from {image_url}")
                img_embedding = get_image_embedding(image_url)
                if img_embedding:
                    all_image_embeddings.append(img_embedding)
                    # ID for image embedding can be related to the text unique_id or be the same if 1-to-1
                    image_unique_id = f"img_{unique_id}" 
                    all_image_ids.append(image_unique_id)
                    all_image_metadata.append({
                        "id": image_unique_id, # Storing the ID itself in metadata for reference
                        "symbol_id": unique_id, # Link back to the text symbol ID
                        "symbol_name": symbol_name,
                        "image_url": image_url,
                        "original_meaning": meaning, # Add the original meaning here
                        "source": "toyota_dashboard_symbols_csv_image"
                    })
                else:
                    print(f"Could not generate embedding for image: {image_url} for symbol '{symbol_name}'")
            else:
                print(f"No image_url for symbol '{symbol_name}', skipping image embedding.")

    if not all_texts:
        print("No valid symbols found to process.")
        return

    print(f"Prepared {len(all_texts)} symbols for embedding.")

    # Use create_embeddings for batch processing
    text_embeddings_list = create_embeddings(all_texts, batch_size=50) # Adjust batch_size if needed

    print(f"Generated {len(text_embeddings_list)} text embeddings.")

    # Store text embeddings in ChromaDB
    # Your store_embeddings function will need to handle a list of texts, their embeddings, and metadata.
    # It might need adjustments to specify the collection name.
    # We need to ensure store_embeddings can handle this format and the specified collection.
    
    if text_embeddings_list and len(text_embeddings_list) == len(all_texts):
        # Placeholder for actual storage logic.
        # We need to call a function like: 
        # success = store_data_in_chroma(texts=all_texts, embeddings=text_embeddings_list, metadata=all_metadata, collection_name=CHROMA_COLLECTION_NAME)
        # This function needs to exist in chroma_store.py or be created.
        # print(f"Attempting to store {len(text_embeddings_list)} embeddings into ChromaDB collection '{CHROMA_COLLECTION_NAME}'.")
        # print("Placeholder: Actual call to chroma_store.store_data_in_chroma would happen here.")
        # For now, simulate success
        # In a real scenario, you'd get a status from the store_embeddings function.
        # print("Symbol ingestion process placeholder finished successfully (simulated storage).")

        # Extract the list of IDs from the metadata we prepared
        text_ids_to_store = [meta["id"] for meta in all_metadata]

        try:
            print(f"Storing {len(text_embeddings_list)} text embeddings into ChromaDB collection '{CHROMA_COLLECTION_NAME}'.")
            storage_result = store_embeddings(
                texts=all_texts,
                embeddings=text_embeddings_list, # Renamed for clarity
                ids=text_ids_to_store, 
                collection_name=CHROMA_COLLECTION_NAME,
                metadata=all_metadata
            )
            print(f"Successfully stored {storage_result.get('stored_count')} text-based symbols in collection '{storage_result.get('collection_name')}'.")
        except Exception as e:
            print(f"Error storing text symbols in ChromaDB: {e}")

        # Now store image embeddings if any were generated
        if all_image_embeddings and len(all_image_embeddings) == len(all_image_ids) == len(all_image_metadata):
            try:
                print(f"Storing {len(all_image_embeddings)} image embeddings into ChromaDB collection '{IMAGE_EMBEDDINGS_COLLECTION_NAME}'.")
                # Note: store_embeddings expects 'texts' as an argument. For image embeddings, 
                # we don't have a direct textual representation of the image itself being stored *as the document*.
                # We can pass the image_url or symbol_name as the 'document' for reference if needed by store_embeddings.
                # Let's use image_url as the 'document' for this collection for now.
                image_documents_for_chroma = [meta['image_url'] for meta in all_image_metadata]

                image_storage_result = store_embeddings(
                    texts=image_documents_for_chroma, # Using image_url as the "document"
                    embeddings=all_image_embeddings,
                    ids=all_image_ids,
                    collection_name=IMAGE_EMBEDDINGS_COLLECTION_NAME,
                    metadata=all_image_metadata
                )
                print(f"Successfully stored {image_storage_result.get('stored_count')} image embeddings in collection '{image_storage_result.get('collection_name')}'.")
            except Exception as e:
                print(f"Error storing image embeddings in ChromaDB: {e}")
        else:
            if not all_image_embeddings:
                print("No image embeddings were generated to store.")
            else:
                print("Mismatch in image embeddings, IDs, or metadata counts. Skipping image embedding storage.")
        
        print("Symbol ingestion process finished.") # Unified end message

    else:
        print("Error: Number of text embeddings does not match number of texts. Skipping text symbol storage.")
        # Also inform about image embeddings if relevant
        if not all_image_embeddings:
            print("Additionally, no image embeddings were generated.")


if __name__ == "__main__":
    # This allows running the script directly for ingestion
    # Ensure your OpenAI API key and ChromaDB client are configured/initialized
    # appropriately before calling this.
    process_and_embed_symbols() 