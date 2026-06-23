"""
Index IDBI synthetic datasets into Pinecone — one namespace per language.
Run once after receiving datasets at orientation / shortlist phase.

Usage:
  python ai/rag/index_datasets.py --dataset-dir ./data --languages en,hi
"""
import os
import argparse
from pinecone import Pinecone, ServerlessSpec

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
INDEX_NAME = os.getenv("PINECONE_INDEX", "wealthseva-idbi")
NAMESPACES = {"en": "idbi-data-en", "hi": "idbi-data-hi", "mr": "idbi-data-mr", "ta": "idbi-data-ta", "bn": "idbi-data-bn"}

def ensure_index():
    if INDEX_NAME not in [i.name for i in pc.list_indexes()]:
        pc.create_index(INDEX_NAME, dimension=1536, metric="cosine",
                        spec=ServerlessSpec(cloud="aws", region="ap-southeast-1"))
        print(f"Created Pinecone index: {INDEX_NAME}")

def index_file(filepath: str, language: str):
    """Chunk a dataset file and upsert into Pinecone namespace."""
    # TODO: Replace with actual embeddings once IDBI datasets are received
    print(f"Indexing {filepath} → namespace: {NAMESPACES[language]}")
    # Chunking + embedding logic goes here

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", default="./data")
    parser.add_argument("--languages", default="en,hi")
    args = parser.parse_args()

    ensure_index()
    for lang in args.languages.split(","):
        print(f"\nIndexing language: {lang}")
        # Walk dataset dir and index each file
        for root, _, files in os.walk(args.dataset_dir):
            for file in files:
                if file.endswith(".csv") or file.endswith(".json"):
                    index_file(os.path.join(root, file), lang.strip())
    print("\nIndexing complete.")
