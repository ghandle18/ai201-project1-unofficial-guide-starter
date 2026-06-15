# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

<!-- What domain did you choose? Why is this knowledge valuable and hard to find through official channels? -->
This system is a TA-verified course information assistant for CS 301: Language & Automata at UIC (University of Illinois Chicago). It makes two categories of knowledge searchable and answerable through a single natural-language interface:

1. Official course knowledge: syllabus policies, exam schedule, grading breakdowns, course calendar - sourced directly from course documents and approved by course staffs.
2. Unofficial but verified knowledge: instructor teaching style, exam preparation strategies, common student misconceptions, recurring Piazza questions, compiled and manually verified by Teaching Assistants based on lived course experience, Rate My Professors, Reddit, and two semesters of Piazza history.

This knowledge is valuable and hard to find through official channels for two reasons:
First, the official UIC course catalog and course website describe "what" the course covers but don't know "how" to succeed in it, they don't tell students which proof techniques appear most on exams, what the most common pumping lemma misconception is, or how the instructor weights CFG derivations vs. DFA minimization. Second, student-generated knowledge (Reddit posts, RMP reviews, Piazza threads) exists but is scattered, unverified, and often outdates. This system consolidates both official and unofficial knowledge into one queryable, grounded, and TA-approved source of truth.

The system is designed with a "contribution loop": when the system cannot confidently answer a question, it redirects students to an anonymous Google Form where they can submit the question to course staff, who manually verify and add it to the document base, making the system self-improving across semesters.
 

---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->
All documents were manually composed or curated by the course TA from official course materials (syllabus, lecture slides, homework assignments, exams) and compiled student knowledge sources (Piazza history, Rate My Professors, Reddit). All instructor and student identities are anonymized. Documents are tagged with an `authority_level` field (`official` or `ta-verified`) stored as ChromaDB metadata.

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | CS 301 official syllabus | Course schedule, topic order, exam/quiz/lab/HW dates — Q&A format | documents/cs301_course_schedule.txt |
| 2 | CS 301 official syllabus | Late penalty, grading breakdown, academic integrity, office hours — Q&A format | documents/cs301_syllabus_policies.txt |
| 3 | CS 301 lecture slides + HW1 (rewritten by TA) | DFA/NFA construction patterns, Kleene star, closure proofs | documents/cs301_topic_dfa_nfa.txt |
| 4 | CS 301 lecture slides + HW2 (rewritten by TA) | Regular expression idioms, pumping lemma proof structure + worked examples | documents/cs301_topic_regular_languages.txt |
| 5 | CS 301 lecture slides + HW3 (rewritten by TA) | CFG design strategies, CNF procedure, PDA construction, ambiguity proofs | documents/cs301_topic_cfg_pda.txt |
| 6 | CS 301 lecture slides + HW4 (rewritten by TA) | CFL pumping lemma, TM implementation-level descriptions | documents/cs301_topic_turing_machines.txt |
| 7 | CS 301 HW5 + lecture (rewritten by TA) | Decidability proofs via subroutine TMs, undecidability via A_TM reduction | documents/cs301_exam_prep.txt |
| 8 | CS 301 HW6 + lecture (rewritten by TA) | Class P proofs with runtime analysis, NP membership via nondeterministic TM | documents/cs301_lab_guide.txt |
| 9 | CS 301 Exam 1 & 2 prep (compiled by TA) | Actual problem types, True/False analysis, GNFA conversion, subset construction | documents/cs301_piazza_faq.txt |
| 10 | CS 301 Final exam prep (compiled by TA) | Key definitions, closure facts, practice final problem types | documents/cs301_instructor_profile.txt |
| 11 | CS 301 course appendix (official) | Every decidable/undecidable language with proof approach — reference sheet | documents/cs301_decidability_reference.txt |

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

This corpus contains three structurally distinct document types. A single fixed-character splitter would be inappropriate, it would break Q&A pairs mid-answer and split multi-step proof examples across chunk boundaries, destroying the semantic coherence that makes chunks individually retrievable.

**Chunk size:**
Three strategies matched to document type:
- **Type A - Q&A documents** (course schedule, syllabus policies, exam prep, piazza FAQ, lab guide): Variable, bounded at ~600 characters. Split on `Q:` boundary markers, each chunk = one complete Q&A pair.
- **Type B - Structured lecture content** (DFA/NFA, regular languages, CFG/PDA, Turing machines, decidability reference): ~500-800 characters. Split on `Topic:` headers - each chunk = one complete concept unit (Definition + Example + Key insight).
- **Type C - Narrative/profile** (instructor profile, final exam prep): ~300-500 characters per paragraph. Split on `\n\n` paragraph boundaries.

**Overlap:**
- Type A: ~50 characters. Q&A pairs are self-contained — minimal overlap needed.
- Type B: ~80 characters (~1 sentence). Concepts often motivate each other; overlap preserves connective tissue across topic boundaries.
- Type C: ~60 characters. Adjacent profile paragraphs are thematically related.

**Reasoning:**
A Q&A pair is the natural unit of meaning in Type A documents. Splitting mid-answer means neither chunk is independently retrievable. For Type B, a pumping lemma proof or subset construction example only makes sense as a complete unit: setup + example + key insight together. Breaking mid-proof produces a chunk that matches queries topically but fails to help the student. Type C has no structural markers, so paragraph-level splitting preserves the natural discourse unit.
 
Final chunk count: 136 chunks across 11 documents.

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:** `all-MiniLM-L6-v2` via `sentence-transformers` (local, no API key, no rate limits)

**Top-k:** 5

Rationale for top-k = 5: 
CS 301 questions often have answers distributed across multiple document types. A question like "How should I prepare for the CFG exam?" may need one chunk from exam prep (strategy), one from the CFG topic file (content), and one from piazza FAQ (common mistakes). Top-5 provides enough coverage without over-diluting the LLM context with loosely related material.
 
Confidence tiering based on cosine distance:
- Distance < 0.30 -> High confidence: answer cited directly
- Distance 0.30–0.55 -> Medium confidence: answer cited with "verify with TA" note
- Distance > 0.55 -> Low confidence: system declines, redirects to contribution form

**Production tradeoff reflection:**
`all-MiniLM-L6-v2` is appropriate for a local prototype — no API cost, runs on CPU under 100ms. For production deployment serving ~200 students per semester:
- **Domain specificity:** The model was trained on general text, not CS theory notation (δ, Σ*, ε-transitions). A fine-tuned model on math/CS corpora (e.g., `allenai/scibert_scivocab_uncased`) would improve retrieval for formal notation queries.
- **Context length:** MiniLM truncates at 256 tokens. Multi-step proof chunks near 800 characters risk truncation. `all-mpnet-base-v2` (512 tokens) is the natural local upgrade.
- **Multilingual support:** UIC has significant international enrollment. `multilingual-e5-large` would support non-English queries retrieving English documents correctly.
- **Latency vs. accuracy:** Local models give consistent ~80ms latency. API-hosted models (OpenAI `text-embedding-3-large`) offer higher accuracy but add network variance and per-call cost.

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | What is the late submission penalty for homework in CS 301? | 0–12 hours late: 5-point penalty. 12–24 hours late: 10-point penalty. More than 24 hours: not accepted (0 points). |
| 2 | What is the subset construction algorithm and what is the worst-case number of states in the resulting DFA if the input NFA has n states? | Subset construction converts an NFA to an equivalent DFA by treating sets of NFA states as single DFA states. Worst case: 2^n states. |
| 3 | Which topics are weighted most heavily on CS 301 exams? | Regular languages (DFA/NFA, pumping lemma) on Exam 1; CFGs and PDAs on Exam 2; Turing machines, decidability, and complexity on the Final. |
| 4 | What is the most common mistake students make with the pumping lemma for regular languages? | Students frequently treat the pumping length p as something they choose, when in fact the adversary chooses p. The correct proof structure requires the argument to work for ALL valid splits, not just one chosen split. |
| 5 | What is this course about, when are the exams, and which TA sections are recommended? | Requires combining three sources: course overview (syllabus), exam schedule (course schedule), and TA/lab guidance (lab guide). Designed as cross-document failure case. |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1. **Formal notation outside embedding model vocabulary:**
`all-MiniLM-L6-v2` was trained on general text. Symbols like δ (transition function), Σ*, and ε-transitions may embed poorly, causing vocabulary mismatch failures where a query using formal notation doesn't retrieve the correct chunk. 
- Mitigation: All lecture documents include both formal notation AND natural language descriptions in the same chunk, so natural-language queries still find relevant content. 
- Observed: Query "What is the subset construction algorithm?" returned LOW confidence (top distance: 0.66) because the document used "NFA to DFA conversion" rather than "subset construction" as primary phrasing.

2. **Authority conflict between syllabus and compiled Piazza/TA content.** The syllabus represents fixed official policy. Piazza announcements may reflect instructor updates that contradict the syllabus (ex: class-wide extensions granted after the fact). 
- Mitigation: Each chunk carries `authority_level` metadata (`official` vs `ta-verified`), and the system prompt instructs the LLM to cite authority level and surface both when conflict is detected. 
- Remaining limitation: Conflict detection is not automated, the LLM handles it via prompt instruction only.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->
```
Raw Sources (Syllabus PDF, Lecture Slides, HW Assignments, Exams, Piazza, RMP)
     │
     ▼
[Manual TA Curation + Anonymization]
 Rewrite into structured .txt files
 Assign: source_type, authority_level metadata
     │
     ▼
[ingest.py]
 Type-aware chunking (dispatch by doc_type):
   - Q&A docs     → split on "Q:" boundary    (~600 chars, overlap ~50)
   - Lecture docs → split on "Topic:" boundary (~500-800 chars, overlap ~80)
   - Narrative    → split on "\n\n"            (~300-500 chars, overlap ~60)
 Output: 136 chunks with text + metadata
     │
     ▼
[embed.py]
 Embed with all-MiniLM-L6-v2 (sentence-transformers)
 Store in ChromaDB (cosine similarity, persistent at ./chroma_db/)
 Metadata: source, authority_level, source_type, doc_type, chunk_index
     │
     ▼  ◄──── Student query (Gradio UI)
[query.py]
 Embed query → retrieve top-5 chunks (ChromaDB cosine search)
 Apply confidence tiering (distance thresholds: <0.30 / 0.30-0.55 / >0.55)
 Build grounded prompt with authority labels per chunk
     │
     ▼
[Groq LLM — llama-3.3-70b-versatile]
 System prompt: answer ONLY from retrieved context
 Cite source filename + authority level per claim
 If low confidence: redirect to Google Form contribution loop
     │
     ▼
[app.py — Gradio UI]
 Input: student question
 Output: grounded answer + confidence label + sources used
 Collapsible: retrieved chunks with distances (debug view)
```
---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 1-2 - Ideations, Documents & Planning:**
Firstly when reading the project, I was not having enough context/ idea about this project, I asked Claude to explain further for me, then brainstormed my own idea based on the Teaching Assistant experience in CS 301 at UIC & propose this finetuned pipeline as an intervention that could potentially turn into a good practice for a future CSEd research project. I extracted part of the teaching materials (anonymized for Claude to help generate such 10 documents that fit my brainstormed idea as .txt file to meet the timing requirements) **- Milestone 1.**

Then for this planning.md, I of course draft the idea myself, then asked Claude to refine the idea and co-work with me to complete this document with the most relevant details, then commit & also generate the ASCII Project Architecture based on the information we discussed! **- Milestone 2.**

**Milestone 3 — Ingestion and chunking:**
I gave Claude the Chunking Strategy section of this planning.md: specifically the three document types, their boundary markers (Q:, Topic:, \n\n), chunk sizes, and overlap values; and asked it to implement a `chunk_document(text, doc_type)` function in `ingest.py` that dispatches to the correct strategy based on `doc_type`. I verified the output by running `python ingest.py` and inspecting 5 random chunks to check that Q&A pairs were intact, lecture concept units included Definition + Example + Key insight together, and no chunk was shorter than 30 characters or longer than 900 characters. 
Final chunk count: 136.

**Milestone 4 — Embedding and retrieval:**
I gave Claude the Retrieval Approach section and the architecture diagram and asked it to implement `embed.py` (load chunks -> embed with `all-MiniLM-L6-v2` → store in ChromaDB with metadata fields: `source`, `authority_level`, `source_type`, `doc_type`, `chunk_index`) and a `retrieve(query, top_k=5)` function in `query.py` returning chunks with distance scores. I verified by running 3 evaluation queries and checking that top results had distances below 0.5 and visibly related content. I also observed the vocabulary mismatch failure on the subset construction query (distance 0.66) and documented it as the anticipated challenge.

**Milestone 5 — Generation and interface:**
I gave Claude the grounding requirement (answer ONLY from retrieved context, cite authority level, redirect to Google Form if low confidence), the confidence tiering thresholds, and the Gradio skeleton from the project spec. I asked it to implement the full `ask()` function and `app.py`. I directed Claude to add a third output panel for confidence label (not in the original spec skeleton) and a collapsible debug view showing retrieved chunks with distance scores. I also overrode the initial system prompt: Claude's first draft said "use the provided context" which is too soft; I directed it to say "Answer ONLY using information from the retrieved documents. Do not use any outside knowledge" with an explicit fallback instruction for low-confidence cases.