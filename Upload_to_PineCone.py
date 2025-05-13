#!/usr/bin/env python3
import json
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec
import time

# === CONFIG ===
PINECONE_API_KEY = "pcsk_P2eEA_fRgbzagr1ES3BeTaS6XwXVztjwbCKf9Qpev1PYZ3yxrRHoG1XsnyNcTEcUPDRt"
INDEX_NAME = "car-llm"
JSON_PATH = "/Users/christianchen/Desktop/Education/DataRes/CarLLM/camry_text_by_page.json"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# === INIT PINECONE ===
pc = Pinecone(api_key=PINECONE_API_KEY)

# Create index if it doesn't exist
if INDEX_NAME not in pc.list_indexes().names():
    pc.create_index(
        name=INDEX_NAME,
        dimension=384,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )
    # Wait for index to be ready
    while pc.describe_index(INDEX_NAME).status['ready'] is False:
        print("⏳ Waiting for Pinecone index to be ready...")
        time.sleep(2)

index = pc.Index(INDEX_NAME)

# === LOAD DATA ===
with open(JSON_PATH, "r") as f:
    pages = json.load(f)

# === LOAD EMBEDDING MODEL ===
print("🔄 Loading embedding model...")
model = SentenceTransformer(EMBEDDING_MODEL)

# === BUILD VECTORS ===
vectors = []
print("🔁 Embedding and batching pages...")
for page in pages:
    page_id = f"page_{page['page']}"
    text = page["text"]
    embedding = model.encode(text).tolist()
    vectors.append((page_id, embedding, {"page": page["page"], "text": text}))

# === UPLOAD TO PINECONE ===
print(f"🚀 Uploading {len(vectors)} vectors to Pinecone...")
index.upsert(vectors=vectors)
print("✅ Upload complete.")
