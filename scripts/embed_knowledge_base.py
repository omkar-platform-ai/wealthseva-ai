#!/usr/bin/env python3
"""
Embed the local knowledge base with Amazon Titan Text Embeddings V2.

Writes backend/data/knowledge_base_embeddings.json, which rag_service loads
for in-memory semantic retrieval (multilingual — Titan v2 embeds Indic-script
queries into the same space as the English KB chunks).

Run ONCE after any knowledge_base.json change, then commit the output file:

    backend/venv/bin/python scripts/embed_knowledge_base.py [--region ap-south-1]

NOTE (2026-07-05): this AWS account currently has quota 0 RPM for on-demand
Titan V2 inference in every region ("ThrottlingException" on the very first
call) — same escalation as the Claude daily-token quota. Until AWS raises it,
this script cannot run; rag_service degrades to (vernacular-aware) keyword
matching automatically. Reruns are resumable: already-embedded chunks are
skipped when the KB hash matches.
"""
import argparse
import hashlib
import json
import os
import sys
import time

import boto3
from botocore.config import Config

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB_PATH = os.path.join(REPO_ROOT, "backend", "data", "knowledge_base.json")
OUT_PATH = os.path.join(REPO_ROOT, "backend", "data", "knowledge_base_embeddings.json")
MODEL_ID = "amazon.titan-embed-text-v2:0"
DIMENSIONS = 1024  # must match _embed_query_sync in backend/services/rag_service.py


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--region", default="ap-south-1")
    parser.add_argument("--pace", type=float, default=1.0,
                        help="seconds to sleep between calls (be gentle on RPM quota)")
    args = parser.parse_args()

    with open(KB_PATH, "rb") as f:
        kb_bytes = f.read()
    kb_sha256 = hashlib.sha256(kb_bytes).hexdigest()
    chunks = json.loads(kb_bytes)

    # Resume: keep embeddings from a previous run against the identical KB.
    embeddings: dict = {}
    if os.path.exists(OUT_PATH):
        with open(OUT_PATH) as f:
            previous = json.load(f)
        if previous.get("kb_sha256") == kb_sha256 and previous.get("model_id") == MODEL_ID:
            embeddings = previous.get("embeddings", {})
            print(f"Resuming: {len(embeddings)}/{len(chunks)} chunks already embedded")

    client = boto3.client(
        "bedrock-runtime",
        region_name=args.region,
        config=Config(retries={"max_attempts": 2}),
    )

    todo = [c for c in chunks if c["id"] not in embeddings]
    for i, chunk in enumerate(todo, 1):
        # Topic prefix gives the embedding a little extra context
        text = f"{chunk.get('topic', '')}. {chunk['text']}"
        body = json.dumps({"inputText": text, "dimensions": DIMENSIONS, "normalize": True})
        for attempt in range(5):
            try:
                response = client.invoke_model(modelId=MODEL_ID, body=body)
                vector = json.loads(response["body"].read())["embedding"]
                # 6 decimals keeps the file small; cosine ranking is unaffected
                embeddings[chunk["id"]] = [round(x, 6) for x in vector]
                print(f"[{i}/{len(todo)}] {chunk['id']} ok")
                break
            except Exception as e:
                wait = 2 ** attempt * 5
                print(f"[{i}/{len(todo)}] {chunk['id']} failed ({e}); retry in {wait}s")
                time.sleep(wait)
        else:
            _write(kb_sha256, embeddings)
            print(f"ABORTED after persistent failures — progress saved "
                  f"({len(embeddings)}/{len(chunks)}); rerun to resume.")
            return 1
        time.sleep(args.pace)

    _write(kb_sha256, embeddings)
    print(f"Done: {len(embeddings)}/{len(chunks)} embeddings -> {OUT_PATH}")
    print("Commit the file so it ships with the Docker image.")
    return 0


def _write(kb_sha256: str, embeddings: dict) -> None:
    with open(OUT_PATH, "w") as f:
        json.dump(
            {
                "model_id": MODEL_ID,
                "dimensions": DIMENSIONS,
                "kb_sha256": kb_sha256,
                "embeddings": embeddings,
            },
            f,
        )


if __name__ == "__main__":
    sys.exit(main())
