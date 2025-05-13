#!/usr/bin/env python3

#!/usr/bin/env python3
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
import os

# === CONFIG ===
PINECONE_API_KEY = "pcsk_P2eEA_fRgbzagr1ES3BeTaS6XwXVztjwbCKf9Qpev1PYZ3yxrRHoG1XsnyNcTEcUPDRt"
INDEX_NAME = "car-llm"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
TOP_K = 3

# === INIT ===
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(INDEX_NAME)

# Load embedding model
print("🤖 Loading embedding model...")
model = SentenceTransformer(EMBEDDING_MODEL)

def search_manual(query, k=TOP_K):
    # Embed the query
    print(f"🔍 Searching for: \"{query}\"")
    query_embedding = model.encode([query]).tolist()

    # Search Pinecone
    response = index.query(
        vector=query_embedding,
        top_k=k,
        include_metadata=True
    )

    # Display results
    for match in response["matches"]:
        score = match["score"]
        metadata = match["metadata"]
        print(f"\n📄 Page {metadata['page']} (Score: {score:.4f})")
        print(metadata["text"][:600].strip() + "\n...")

# === Example Usage ===
if __name__ == "__main__":
    while True:
        user_query = input("\n🧠 Ask a question (or type 'exit'): ")
        if user_query.lower() == "exit":
            break
        search_manual(user_query)
