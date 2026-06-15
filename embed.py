"""
embed.py — Embed all chunks and store in ChromaDB.
Run once before using query.py or app.py:
    python embed.py

To rebuild from scratch (e.g. after adding documents):
    rm -rf chroma_db/
    python embed.py
"""

import chromadb
from sentence_transformers import SentenceTransformer
from ingest import build_chunks

COLLECTION_NAME = "cs301_unofficial_guide"
CHROMA_PATH = "./chroma_db"


def build_vector_store(docs_dir: str = "documents") -> None:
    print("Loading embedding model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    print("Building chunks from documents...")
    chunks = build_chunks(docs_dir)
    if not chunks:
        print("ERROR: No chunks produced. Check your documents/ folder.")
        return

    print("Connecting to ChromaDB...")
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    # Fresh rebuild each time
    try:
        client.delete_collection(COLLECTION_NAME)
        print("Deleted existing collection.")
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    print(f"Embedding {len(chunks)} chunks...")
    texts = [c["text"] for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=True).tolist()

    ids = [f"{c['source']}__chunk{c['chunk_index']}" for c in chunks]
    metadatas = [{
        "source":      c["source"],
        "doc_type":    c["doc_type"],
        "authority":   c["authority"],
        "source_type": c["source_type"],
        "chunk_index": c["chunk_index"],
    } for c in chunks]

    # Insert in batches of 500 (ChromaDB limit)
    batch_size = 500
    for i in range(0, len(chunks), batch_size):
        collection.add(
            ids=ids[i:i+batch_size],
            embeddings=embeddings[i:i+batch_size],
            documents=texts[i:i+batch_size],
            metadatas=metadatas[i:i+batch_size],
        )

    print(f"\nDone — {len(chunks)} chunks stored in ChromaDB at {CHROMA_PATH}/")
    print(f"Collection: {COLLECTION_NAME}")


if __name__ == "__main__":
    build_vector_store()
