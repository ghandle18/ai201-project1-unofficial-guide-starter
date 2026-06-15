"""
query.py — Retrieval and grounded generation with confidence tiering.

Confidence tiers based on cosine distance of top retrieved chunk:
  < 0.30  → High confidence   (cite directly)
  0.30–0.55 → Medium confidence (cite with verify-with-TA note)
  > 0.55  → Low confidence    (decline, redirect to contribution form)
"""

import os
import chromadb
from sentence_transformers import SentenceTransformer
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

COLLECTION_NAME = "cs301_unofficial_guide"
CHROMA_PATH = "./chroma_db"
TOP_K = 5
CONTRIBUTION_FORM = "https://forms.google.com/your-form-link-here"

# Distance thresholds for confidence tiering
HIGH_CONFIDENCE_THRESHOLD   = 0.30
MEDIUM_CONFIDENCE_THRESHOLD = 0.55

# Module-level singletons
_model      = None
_collection = None
_groq       = None


def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def _get_collection():
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        _collection = client.get_collection(COLLECTION_NAME)
    return _collection


def _get_groq():
    global _groq
    if _groq is None:
        _groq = Groq(api_key=os.environ["GROQ_API_KEY"])
    return _groq


def retrieve(query: str, top_k: int = TOP_K) -> list[dict]:
    """
    Embed query and return top-k most similar chunks with metadata and distance scores.
    Results are sorted closest-first (lowest distance = most relevant).
    """
    model      = _get_model()
    collection = _get_collection()

    query_embedding = model.encode([query]).tolist()[0]
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    # _collection.query() returns nested lists — index [0] for single query
    chunks = []
    for text, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append({
            "text":        text,
            "source":      meta["source"],
            "authority":   meta["authority"],
            "source_type": meta["source_type"],
            "doc_type":    meta["doc_type"],
            "distance":    round(dist, 4),
        })
    return chunks


def _confidence_tier(top_distance: float) -> str:
    if top_distance < HIGH_CONFIDENCE_THRESHOLD:
        return "high"
    elif top_distance < MEDIUM_CONFIDENCE_THRESHOLD:
        return "medium"
    else:
        return "low"


SYSTEM_PROMPT = """You are the CS 301 Unofficial Course Assistant — a TA-verified information \
system for CS 301: Languages & Automata at UIC (University of Illinois Chicago).

RULES — follow these exactly:
1. Answer ONLY using information from the retrieved documents provided below. Do not use \
any outside knowledge, general CS knowledge, or information from your training data.
2. Every factual claim must be cited by document name, e.g. "According to \
cs301_syllabus_policies.txt [official]..."
3. When a document is labeled [authority: official], cite it first and weight it above \
documents labeled [authority: ta-verified].
4. If two retrieved documents conflict, surface BOTH and label their authority levels \
so the student can decide which to trust.
5. If the retrieved documents do not contain enough information to answer confidently, \
you MUST respond with exactly:
"There's no current verified information regarding your question about CS 301 in our \
database. Flag this to course admins & get an up-to-date response by submitting this \
Google Form: {form}. Your questions help us improve the course!"
6. Never infer, extrapolate, or fill gaps with general knowledge. If you don't have it \
in the documents, say so explicitly.""".format(form=CONTRIBUTION_FORM)


def ask(question: str, top_k: int = TOP_K) -> dict:
    """
    Full RAG pipeline: retrieve → confidence tier → generate.

    Returns:
        answer       (str)  — grounded LLM response
        confidence   (str)  — "high", "medium", or "low"
        sources      (list) — deduplicated source filenames
        chunks       (list) — raw retrieved chunks with distances
    """
    chunks = retrieve(question, top_k=top_k)
    top_distance = chunks[0]["distance"] if chunks else 1.0
    confidence = _confidence_tier(top_distance)

    # Low confidence → skip LLM, redirect directly
    if confidence == "low":
        return {
            "answer": (
                f"There's no current verified information regarding your question about "
                f"CS 301 in our database. Flag this to course admins & get an up-to-date "
                f"response by submitting this Google Form: {CONTRIBUTION_FORM}. "
                f"Your questions help us improve the course!"
            ),
            "confidence": "low",
            "sources": [],
            "chunks": chunks,
        }

    # Build context block with authority labels visible to the LLM
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        context_parts.append(
            f"[Document {i}: {chunk['source']} | authority: {chunk['authority']}]\n"
            f"{chunk['text']}"
        )
    context = "\n\n---\n\n".join(context_parts)

    # Medium confidence → add verify note to prompt
    verify_note = ""
    if confidence == "medium":
        verify_note = (
            "\n\nNOTE: The retrieved information has medium confidence. "
            "Remind the student to verify critical details with their TA."
        )

    user_message = (
        f"Retrieved documents:\n\n{context}\n\n---\n\n"
        f"Question: {question}\n\n"
        f"Answer using ONLY the documents above. Cite each source by filename and authority level."
        f"{verify_note}"
    )

    groq = _get_groq()
    response = groq.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_message},
        ],
        max_tokens=700,
        temperature=0.1,  # low temp = more faithful to retrieved context
    )

    answer = response.choices[0].message.content.strip()
    sources = list(dict.fromkeys(c["source"] for c in chunks))  # ordered, deduplicated

    return {
        "answer":     answer,
        "confidence": confidence,
        "sources":    sources,
        "chunks":     chunks,
    }


if __name__ == "__main__":
    """Quick retrieval test — run before app.py to verify pipeline."""
    test_queries = [
        "What is the late submission penalty for homework?",
        "What is the subset construction algorithm?",
        "Which topics are most heavily tested on CS 301 exams?",
    ]
    for q in test_queries:
        print(f"\n{'='*60}")
        print(f"Q: {q}")
        chunks = retrieve(q)
        print(f"Top {len(chunks)} chunks:")
        for c in chunks:
            print(f"  [{c['source']} | {c['authority']} | dist: {c['distance']}]")
            print(f"  {c['text'][:100]}...")
        result = ask(q)
        print(f"\nConfidence: {result['confidence'].upper()}")
        print(f"Answer:\n{result['answer']}")
        print(f"Sources: {result['sources']}")
