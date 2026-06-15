"""
ingest.py — Document loading and type-aware chunking pipeline.

Three document types, three strategies:
  - "qa"        → split on "Q:" boundaries (syllabus, piazza, exam prep, lab guide)
  - "lecture"   → split on "Topic:" boundaries (DFA/NFA, CFG, TM, regular languages)
  - "narrative" → split on paragraph boundaries (instructor profile)

Authority levels are stored as metadata in ChromaDB for confidence tiering in query.py.
"""

import os
import re
from pathlib import Path

# Maps filename → (doc_type, authority_level, source_type)
DOCUMENT_REGISTRY = {
    "cs301_syllabus_policies.txt":     ("qa",        "official",    "syllabus"),
    "cs301_course_schedule.txt":       ("qa",        "official",    "schedule"),
    "cs301_instructor_profile.txt":    ("narrative", "ta-verified", "profile"),
    "cs301_topic_dfa_nfa.txt":         ("lecture",   "ta-verified", "lecture"),
    "cs301_topic_regular_languages.txt":("lecture",  "ta-verified", "lecture"),
    "cs301_topic_cfg_pda.txt":         ("lecture",   "ta-verified", "lecture"),
    "cs301_topic_turing_machines.txt": ("lecture",   "ta-verified", "lecture"),
    "cs301_exam_prep.txt":             ("qa",        "ta-verified", "exam-prep"),
    "cs301_piazza_faq.txt":            ("qa",        "ta-verified", "piazza"),
    "cs301_lab_guide.txt":             ("qa",        "ta-verified", "lab"),
    "cs301_decidability_reference.txt": ("lecture",   "official",    "reference"),
}


def load_documents(docs_dir: str = "documents") -> list[dict]:
    """Load all .txt files from documents/ and tag with registry metadata."""
    documents = []
    docs_path = Path(docs_dir)
    for filepath in sorted(docs_path.glob("*.txt")):
        filename = filepath.name
        if filename not in DOCUMENT_REGISTRY:
            print(f"  [warn] {filename} not in registry — skipping.")
            continue
        doc_type, authority, source_type = DOCUMENT_REGISTRY[filename]
        with open(filepath, "r", encoding="utf-8") as f:
            raw_text = f.read()
        documents.append({
            "source":       filename,
            "doc_type":     doc_type,
            "authority":    authority,
            "source_type":  source_type,
            "raw_text":     raw_text,
        })
    print(f"Loaded {len(documents)} documents.")
    return documents


def clean_text(text: str) -> str:
    """Collapse excessive blank lines and strip trailing whitespace."""
    text = re.sub(r'\n{3,}', '\n\n', text)
    lines = [line.rstrip() for line in text.split('\n')]
    return '\n'.join(lines).strip()


# ── Type A: Q&A boundary chunking ────────────────────────────────────────────

def chunk_qa(text: str, max_chars: int = 600, overlap_chars: int = 50) -> list[str]:
    """
    Split on 'Q:' boundaries. Each chunk = one complete Q&A pair.
    If a single answer exceeds max_chars, split at nearest sentence boundary.
    Overlap carries the last overlap_chars of the previous chunk into the next
    in case a multi-part answer is split.
    """
    # Split on Q: markers, keep the marker
    raw_pairs = re.split(r'(?=\nQ:|\AQ:)', text)
    raw_pairs = [p.strip() for p in raw_pairs if p.strip()]

    chunks = []
    carry = ""
    for pair in raw_pairs:
        candidate = (carry + " " + pair).strip() if carry else pair
        if len(candidate) <= max_chars:
            chunks.append(candidate)
            carry = candidate[-overlap_chars:] if len(candidate) > overlap_chars else ""
        else:
            # Split long pair at sentence boundary after max_chars/2
            split_point = max_chars // 2
            sentences = re.split(r'(?<=[.?!])\s+', candidate)
            current = ""
            for sentence in sentences:
                if len(current) + len(sentence) > max_chars and current:
                    chunks.append(current.strip())
                    carry = current[-overlap_chars:]
                    current = carry + " " + sentence
                else:
                    current += (" " if current else "") + sentence
            if current.strip():
                chunks.append(current.strip())
                carry = current[-overlap_chars:]

    return [c for c in chunks if len(c) >= 30]


# ── Type B: Lecture/Topic boundary chunking ───────────────────────────────────

def chunk_lecture(text: str, max_chars: int = 800, overlap_chars: int = 80) -> list[str]:
    """
    Split on 'Topic:' headers. Each chunk = one concept unit
    (Topic + Definition + Example + Key insight).
    Overlap preserves the last sentence of one concept into the next
    because concepts often motivate each other.
    """
    raw_topics = re.split(r'(?=\nTopic:|\ATopic:)', text)
    raw_topics = [t.strip() for t in raw_topics if t.strip()]

    chunks = []
    carry = ""
    for topic in raw_topics:
        candidate = (carry + "\n\n" + topic).strip() if carry else topic
        if len(candidate) <= max_chars:
            chunks.append(candidate)
            carry = candidate[-overlap_chars:] if len(candidate) > overlap_chars else ""
        else:
            # Split at paragraph boundary within the topic
            paras = [p.strip() for p in candidate.split('\n\n') if p.strip()]
            current = ""
            for para in paras:
                if len(current) + len(para) > max_chars and current:
                    chunks.append(current.strip())
                    carry = current[-overlap_chars:]
                    current = carry + "\n\n" + para
                else:
                    current += ("\n\n" if current else "") + para
            if current.strip():
                chunks.append(current.strip())
                carry = current[-overlap_chars:]

    return [c for c in chunks if len(c) >= 30]


# ── Type C: Narrative/paragraph chunking ──────────────────────────────────────

def chunk_narrative(text: str, max_chars: int = 500, overlap_chars: int = 60) -> list[str]:
    """
    Split on paragraph (\\n\\n) boundaries.
    Each chunk = one coherent biographical or descriptive paragraph.
    Overlap carries thematic continuity between adjacent paragraphs.
    """
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    chunks = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) + 2 > max_chars and current:
            chunks.append(current.strip())
            current = current[-overlap_chars:] + "\n\n" + para
        else:
            current += ("\n\n" if current else "") + para

    if current.strip():
        chunks.append(current.strip())

    return [c for c in chunks if len(c) >= 30]


# ── Dispatcher ────────────────────────────────────────────────────────────────

def chunk_document(text: str, doc_type: str) -> list[str]:
    """Dispatch to the correct chunking strategy based on document type."""
    if doc_type == "qa":
        return chunk_qa(text)
    elif doc_type == "lecture":
        return chunk_lecture(text)
    elif doc_type == "narrative":
        return chunk_narrative(text)
    else:
        raise ValueError(f"Unknown doc_type: {doc_type!r}. Expected 'qa', 'lecture', or 'narrative'.")


# ── Full pipeline ─────────────────────────────────────────────────────────────

def build_chunks(docs_dir: str = "documents") -> list[dict]:
    """
    Full pipeline: load → clean → chunk.
    Returns list of dicts: {source, doc_type, authority, source_type, chunk_index, text}
    """
    documents = load_documents(docs_dir)
    all_chunks = []

    for doc in documents:
        cleaned = clean_text(doc["raw_text"])
        chunks = chunk_document(cleaned, doc["doc_type"])
        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "source":      doc["source"],
                "doc_type":    doc["doc_type"],
                "authority":   doc["authority"],
                "source_type": doc["source_type"],
                "chunk_index": i,
                "text":        chunk,
            })

    print(f"Produced {len(all_chunks)} total chunks from {len(documents)} documents.")
    return all_chunks


if __name__ == "__main__":
    chunks = build_chunks()
    print("\n--- 5 Sample Chunks ---\n")
    import random
    sample = random.sample(chunks, min(5, len(chunks)))
    for c in sample:
        print(f"[{c['source']} | {c['doc_type']} | authority: {c['authority']} | chunk #{c['chunk_index']}]")
        print(c['text'])
        print()
