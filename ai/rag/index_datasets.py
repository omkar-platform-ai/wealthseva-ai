"""
Index IDBI synthetic datasets into Pinecone — one namespace per language.
Run once after receiving datasets at orientation / shortlist phase.

For MVP: Creates mock_index.json as fallback when Pinecone is not configured.

Usage:
  python ai/rag/index_datasets.py
"""
import os
import json
import csv


def create_mock_index():
    """Create mock_index.json from sample_transactions.csv for keyword matching fallback."""
    # Get the project root (wealthseva-ai directory)
    # index_datasets.py is at: wealthseva-ai/ai/rag/index_datasets.py
    # So we go up two levels to reach wealthseva-ai
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    csv_path = os.path.join(project_root, "data/sample_transactions.csv")
    output_path = os.path.join(project_root, "data/mock_index.json")

    print(f"Project root: {project_root}")
    print(f"Looking for CSV at: {csv_path}")

    if not os.path.exists(csv_path):
        print(f"CSV file not found: {csv_path}")
        return

    chunks = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            category = row['category']
            amount = row['amount']
            month = row['month']
            segment = row['customer_segment']
            # Create text chunks in natural language format
            chunk = f"In {month}, a {segment} customer spent ₹{amount} on {category}."
            chunks.append({
                "text": chunk,
                "category": category,
                "amount": amount,
                "month": month,
                "segment": segment
            })

    with open(output_path, 'w') as f:
        json.dump(chunks, f, indent=2)

    print(f"Created mock index with {len(chunks)} chunks: {output_path}")


def index_to_pinecone(dataset_dir: str = "./data", languages: str = "en,hi"):
    """Index datasets into Pinecone (for production use when API key is available)."""
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    if not pinecone_api_key:
        print("PINECONE_API_KEY not set — skipping Pinecone indexing")
        return

    from pinecone import Pinecone, ServerlessSpec

    pc = Pinecone(api_key=pinecone_api_key)
    INDEX_NAME = os.getenv("PINECONE_INDEX", "wealthseva-idbi")
    NAMESPACES = {"en": "idbi-data-en", "hi": "idbi-data-hi", "mr": "idbi-data-mr", "ta": "idbi-data-ta", "bn": "idbi-data-bn"}

    if INDEX_NAME not in [i.name for i in pc.list_indexes()]:
        pc.create_index(INDEX_NAME, dimension=1536, metric="cosine",
                        spec=ServerlessSpec(cloud="aws", region="ap-southeast-1"))
        print(f"Created Pinecone index: {INDEX_NAME}")

    for lang in languages.split(","):
        print(f"\nIndexing language: {lang}")
        # Walk dataset dir and index each file
        for root, _, files in os.walk(dataset_dir):
            for file in files:
                if file.endswith(".csv") or file.endswith(".json"):
                    filepath = os.path.join(root, file)
                    print(f"  Indexing {filepath} → namespace: {NAMESPACES[lang.strip()]}")
                    # TODO: Implement actual chunking + embedding + upsert logic


if __name__ == "__main__":
    print("Creating mock index for MVP fallback...")
    create_mock_index()

    if os.getenv("PINECONE_API_KEY"):
        try:
            print("\nPINECONE_API_KEY is set — also indexing to Pinecone...")
            index_to_pinecone()
        except ImportError as e:
            print(f"\nPinecone module not installed: {e}")
            print("Skipping Pinecone indexing (using mock fallback only)")
    else:
        print("\nPINECONE_API_KEY not set — skipping Pinecone indexing (using mock fallback only)")

    print("\nIndexing complete.")
