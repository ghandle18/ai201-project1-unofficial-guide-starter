# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

<!-- What topic or category of knowledge does your system cover?
     Why is this knowledge valuable, and why is it hard to find through official channels?
     Example: "Student reviews of CS professors at [university] — useful because official
     course descriptions don't reflect teaching style, exam difficulty, or workload." -->
This system is a **TA-verified course information assistant for CS 301: Languages & Automata at UIC (University of Illinois Chicago)**. It makes two categories of knowledge searchable and answerable through a single natural-language interface:
 
1. **Official course knowledge** — syllabus policies, grading breakdowns, exam schedule, course calendar — sourced directly from official course documents and approved by course staff.
2. **Unofficial but verified knowledge** — exam preparation strategies, common student misconceptions, and recurring Piazza questions — compiled and manually verified by the course Teaching Assistant based on two semesters of Piazza history, Rate My Professors, Reddit, and direct TA observation.
This knowledge is valuable and hard to find through official channels for two reasons. First, the official UIC course catalog and course website describe *what* CS 301 covers but not *how* to succeed — they don't tell students which proof techniques appear most on exams, what the most common pumping lemma misconception is, or how the instructor weights CFG derivations vs. DFA minimization. Second, student-generated knowledge exists on Reddit and Rate My Professors but is scattered, unverified, and often outdated. This system consolidates both into one queryable, grounded, and TA-approved source of truth, with a **contribution loop**: when the system cannot confidently answer, it redirects students to an anonymous Google Form so course staff can manually verify and add the answer — making the system self-improving across semesters.
---

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->
All documents were manually composed or curated by the course TA from official course materials (syllabus, lecture slides, homework assignments, exams) and compiled student knowledge sources (Piazza history, Rate My Professors, Reddit). All instructor and student identities are anonymized. Documents carry `authority_level` metadata (`official` or `ta-verified`) stored in ChromaDB.

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | CS 301 official syllabus | Schedule Q&A (official) | documents/cs301_course_schedule.txt |
| 2 | CS 301 official syllabus | Policies Q&A (official) | documents/cs301_syllabus_policies.txt |
| 3 | CS 301 lecture slides + HW1 (rewritten by TA) | Lecture content (ta-verified) | documents/cs301_topic_dfa_nfa.txt |
| 4 | CS 301 lecture slides + HW2 (rewritten by TA) | Lecture content (ta-verified) | documents/cs301_topic_regular_languages.txt |
| 5 | CS 301 lecture slides + HW3 (rewritten by TA) | Lecture content (ta-verified) | documents/cs301_topic_cfg_pda.txt |
| 6 | CS 301 lecture slides + HW4 (rewritten by TA) | Lecture content (ta-verified) | documents/cs301_topic_turing_machines.txt |
| 7 | CS 301 HW5 + lecture (rewritten by TA) | Exam prep Q&A (ta-verified) | documents/cs301_exam_prep.txt |
| 8 | CS 301 HW6 + lecture (rewritten by TA) | Lab guide Q&A (ta-verified) | documents/cs301_lab_guide.txt |
| 9 | CS 301 Exam 1 & 2 prep (compiled by TA) | Piazza FAQ Q&A (ta-verified) | documents/cs301_piazza_faq.txt |
| 10 | CS 301 Final exam prep (compiled by TA) | Instructor profile narrative (ta-verified) | documents/cs301_instructor_profile.txt |
| 11 | CS 301 course appendix (official) | Decidability reference (official) | documents/cs301_decidability_reference.txt |

---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->
This corpus contains three structurally distinct document types. A single fixed-character splitter would break Q&A pairs mid-answer and split multi-step proof examples across chunk boundaries — destroying the semantic coherence that makes individual chunks retrievable.

**Chunk size:**
- **Type A — Q&A documents** (cs301_course_schedule, cs301_syllabus_policies, cs301_exam_prep, cs301_piazza_faq, cs301_lab_guide): Variable, bounded at ~600 characters. Split on `Q:` boundary markers — each chunk = one complete Q&A pair.
- **Type B — Structured lecture content** (cs301_topic_*.txt, cs301_decidability_reference): ~500–800 characters. Split on `Topic:` headers — each chunk = one complete concept unit (Definition + Example + Key insight).
- **Type C — Narrative/profile** (cs301_instructor_profile): ~300–500 characters per paragraph. Split on `\n\n` boundaries.

**Overlap:**
- Type A: ~50 characters. Q&A pairs are self-contained — minimal overlap needed.
- Type B: ~80 characters (~1 sentence). Concepts often motivate each other; overlap preserves connective tissue across topic boundaries.
- Type C: ~60 characters. Adjacent profile paragraphs are thematically related.

**Why these choices fit your documents:**
A Q&A pair is the natural unit of meaning in Type A documents — splitting mid-answer means neither chunk is independently retrievable. For Type B, a pumping lemma proof or subset construction example only makes sense as a complete unit (setup + example + key insight). Breaking mid-proof produces a chunk that matches queries topically but fails to help the student. Type C lacks structural markers so paragraph-level splitting preserves the natural discourse unit of narrative prose.

**Final chunk count:** 136 chunks across 11 documents.

## Sample Chunks
 
**Chunk 1 — [cs301_syllabus_policies.txt | qa | authority: official | chunk #0]**
```
Q: What is the late submission policy for homework?
A: 0–12 hours late: 5-point penalty. 12–24 hours late: 10-point penalty.
More than 24 hours late: NOT accepted (0 points).
```
 
**Chunk 2 — [cs301_topic_dfa_nfa.txt | lecture | authority: ta-verified | chunk #1]**
```
Q: How do I construct an NFA for Kleene star of a language?
A: The correct construction: Given NFA N with start state q0 and accept states F:
1. Add new start state s that is also an accept state
2. Add ε-transition from s to q0
3. Add ε-transitions from every state in F back to s
This correctly handles ε (via the new accepting start state) and repetition.
```
 
**Chunk 3 — [cs301_exam_prep.txt | qa | authority: ta-verified | chunk #2]**
```
allowed to use known decidable TMs as subroutines. The key ones from class:
- A_DFA: decides whether DFA D accepts string w → always halts
- E_DFA: decides whether L(DFA) = ∅ → always halts
- EQ_DFA: decides whether two DFAs accept the same language → always halts
- A_CFG, E_CFG: similar for CFGs
```
 
**Chunk 4 — [cs301_syllabus_policies.txt | qa | authority: official | chunk #3]**
```
Extra Credit: up to 1% (optional assignments)
 
--- Q: What are the letter grade cutoffs?
A: A: 90–100, B: 80–89, C: 70–79, D: 60–69, F: below 60.
```
 
**Chunk 5 — [cs301_piazza_faq.txt | qa | authority: ta-verified | chunk #5]**
```
Q: How do I construct an NFA for Kleene star of a language?
A: The correct construction (from Exam 1 short answer):
Given NFA N with start state q0 and accept states F:
1. Add new start state s that is also an accept state
2. Add ε-transition from s to q0
3. Add ε-transitions from every state in F back to s
```
 
---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:** `all-MiniLM-L6-v2` via `sentence-transformers` (local, no API key, no rate limits)
 
Chosen because it runs entirely locally — no API cost, no rate limits, consistent ~80ms latency on CPU — appropriate for a prototype that needs to be free and reproducible. Its main limitation for this domain is vocabulary: formal automata theory notation (δ, Σ*, ε-transitions) is out-of-distribution for a model trained on general web text. To mitigate this, all lecture documents include both formal notation AND natural-language descriptions in the same chunk, so natural-language query terms still match.

**Production tradeoff reflection:**
 
For a real deployment serving ~200 students per semester:
- **Domain specificity:** `all-MiniLM-L6-v2` was trained on general text, not CS theory. A model fine-tuned on math/CS corpora (e.g., `allenai/scibert_scivocab_uncased`) would improve retrieval for formal notation queries — this is the system's most significant known limitation.
- **Context length:** MiniLM truncates at 256 tokens. Multi-step proof chunks approaching 800 characters risk losing the key insight at the end. `all-mpnet-base-v2` (512 tokens) is the natural local upgrade.
- **Multilingual support:** UIC has significant international enrollment. `multilingual-e5-large` would allow non-English queries (Vietnamese, Chinese, Spanish) to retrieve English documents correctly via cross-lingual embeddings.
- **Latency vs. accuracy:** Local models give consistent ~80ms latency but have a lower accuracy ceiling. API-hosted models (OpenAI `text-embedding-3-large`) offer higher accuracy but add network latency variance and per-call cost (~$0.00013/1K tokens) — manageable at course scale but worth monitoring during exam-season load spikes.

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:**

```
You are the CS 301 Unofficial Course Assistant — a TA-verified information system
for CS 301: Languages & Automata at UIC (University of Illinois Chicago).
 
RULES — follow these exactly:
1. Answer ONLY using information from the retrieved documents provided below.
   Do not use any outside knowledge, general CS knowledge, or information from
   your training data.
2. Every factual claim must be cited by document name, e.g.
   "According to cs301_syllabus_policies.txt [authority: official]..."
3. When a document is labeled [authority: official], cite it first and weight it
   above documents labeled [authority: ta-verified].
4. If two retrieved documents conflict, surface BOTH and label their authority
   levels so the student can decide which to trust.
5. If the retrieved documents do not contain enough information to answer
   confidently, respond with:
   "There's no current verified information regarding your question about CS 301
   in our database. Flag this to course admins & get an up-to-date response by
   submitting this Google Form: [FORM_LINK]."
6. Never infer, extrapolate, or fill gaps with general knowledge.
```
**How source attribution is surfaced in the response:**
Attribution is enforced at two levels. First, the system prompt explicitly instructs the LLM to cite the document filename and authority level for every factual claim. Second, retrieved chunks are passed to the LLM with their source filename and authority level prepended as a header (e.g., `[Document 1: cs301_syllabus_policies.txt | authority: official]`), making the source visible in context even if the LLM omits it in prose. The Gradio UI displays a separate "Sources Used" panel that programmatically lists all retrieved filenames regardless of LLM behavior — attribution is guaranteed in the UI. Additionally, each response is tagged with a confidence tier (High / Medium / Low) based on the cosine distance of the top retrieved chunk, displayed in a dedicated panel.

---

## Retrieval Test Results
 
**Query 1: "What is the late submission penalty for homework?"**
 
Top chunks returned:
1. [cs301_syllabus_policies.txt | official | dist: 0.18] — "What is the late submission policy for homework..."
2. [cs301_syllabus_policies.txt | official | dist: 0.47] — "Can I submit handwritten work?..."
3. [cs301_syllabus_policies.txt | official | dist: 0.50] — "Where do I submit homework?..."
Why relevant: The top chunk directly contains the late policy Q&A with the specific penalties (0–12hrs: -5pts, 12–24hrs: -10pts, >24hrs: not accepted). Distance 0.18 = high confidence. The query phrase "late submission penalty" matched the document's "late submission policy" despite slight wording difference — semantic search correctly bridged the gap.
 
---
 
**Query 2: "What is the subset construction algorithm?"**
 
Top chunks returned:
1. [cs301_piazza_faq.txt | ta-verified | dist: 0.66] — "How do I convert an NFA to a DFA using subset c..."
2. [cs301_topic_cfg_pda.txt | ta-verified | dist: 0.68] — "SOURCE: CS 301 Homework 3: CFGs & PDAs..."
3. [cs301_lab_guide.txt | ta-verified | dist: 0.70] — "in polynomial time on a standard computer..."
Why relevant: All distances exceeded 0.55 → LOW confidence triggered correctly. The system declined rather than hallucinating. The failure occurred because the document uses "NFA to DFA conversion" as primary phrasing while the query used "subset construction algorithm" — a vocabulary mismatch the general-text embedding model could not bridge. This is the designed failure case.
 
---
 
**Query 3: "Which topics are most heavily tested on CS 301 exams?"**
 
Top chunks returned:
1. [cs301_instructor_profile.txt | ta-verified | dist: 0.38] — "Final Exam Preparation Guide..."
2. [cs301_syllabus_policies.txt | official | dist: 0.45] — "What are the prerequisites for CS 301?..."
3. [cs301_piazza_faq.txt | ta-verified | dist: 0.48] — "Exam 1 & 2: Common Problem Types..."
Why relevant: Cross-document retrieval working correctly — pulled from exam prep, syllabus, and piazza FAQ together. MEDIUM confidence appropriate since no single chunk directly answers "most heavily tested" — the answer requires synthesizing across sources. The LLM correctly combined them into a coherent response.
 
---
 
## Example Responses
 
**Response 1 — Query: "What is the late submission penalty for homework in CS 301?"**
 
```
According to cs301_syllabus_policies.txt [authority: official], the late submission
policy for homework assignments is:
- 0–12 hours late: 5-point penalty
- 12–24 hours late: 10-point penalty
- More than 24 hours late: NOT accepted (0 points)
 
This information is sourced from the official course syllabus policies document.
 
Sources: cs301_syllabus_policies.txt
Confidence: ✅ High
```
 
**Response 2 — Query: "Which topics are weighted most heavily on CS 301 exams?"**
 
```
According to cs301_instructor_profile.txt [authority: ta-verified], the Final Exam
covers Regular Languages, Context-Free Languages, Turing Machines and Decidability,
Undecidability, and Complexity.
 
According to cs301_course_schedule.txt [authority: official], the topic order is:
Weeks 1–5: Regular Languages (DFAs, NFAs, Regular Expressions, Pumping Lemma)
Weeks 6–9: Context-Free Languages (CFGs, PDAs, CFL Pumping Lemma)
Weeks 10–15: Turing Machines, Decidability, Reducibility, Complexity, NP-Completeness
 
According to cs301_piazza_faq.txt [authority: ta-verified], Exam 1 covers DFAs,
NFAs, Regular Expressions, and the Pumping Lemma for Regular Languages.
 
Note: Medium confidence — verify critical exam details with your TA.
 
Sources: cs301_instructor_profile.txt, cs301_course_schedule.txt, cs301_piazza_faq.txt
Confidence: ⚠️ Medium
```
 
**Out-of-scope query — "What is the weather like in Chicago?"**
 
```
There's no current verified information regarding your question about CS 301 in our
database. Flag this to course admins & get an up-to-date response by submitting this
Google Form: https://forms.google.com/your-form-link-here. Your questions help us
improve the course!
 
Confidence: ❌ Low
```
 
---
 
## Query Interface
 
**Interface type:** Gradio web UI (`app.py`) — run with `python app.py`, opens at `http://localhost:7860`
 
**Input fields:**
- *Your question* — free-text question box with 7 pre-loaded example queries
**Output fields:**
- *Answer* — grounded LLM response citing source filenames and authority levels
- *Confidence* — High / Medium / Low based on cosine distance of top retrieved chunk
- *Sources Used* — bulleted list of source filenames (programmatically guaranteed)
- *Retrieved Chunks (debug, collapsible)* — each chunk with source, authority, and distance score
**Setup:**
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python embed.py        # run once to build the vector store
python app.py          # open http://localhost:7860
```
 
**Sample interaction transcript:**
 
```
User: What is the late submission penalty for homework in CS 301?
 
Answer:
According to cs301_syllabus_policies.txt [authority: official], the late submission
policy for homework is: 0–12 hours late: 5-point penalty. 12–24 hours late:
10-point penalty. More than 24 hours late: NOT accepted (0 points).
 
Confidence: ✅ High confidence — answer drawn from verified course documents
Sources Used: • cs301_syllabus_policies.txt
```
 
---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | What is the late submission penalty for homework in CS 301? | 0–12hrs: -5pts, 12–24hrs: -10pts, >24hrs: 0 | Correctly cited all three penalty tiers from cs301_syllabus_policies.txt with authority label [official]. Distance: 0.18. | Relevant | Accurate |
| 2 | What is the subset construction algorithm and what is the worst-case number of states if the NFA has n states? | Subset construction converts NFA→DFA by treating state sets as DFA states. Worst case: 2^n states. | LOW confidence triggered — system declined and redirected to contribution form. Top distance: 0.66. No answer generated. | Off-target | Inaccurate |
| 3 | Which topics are weighted most heavily on CS 301 exams? | Regular languages on Exam 1; CFGs/PDAs on Exam 2; TMs/decidability/complexity on Final. | Correctly synthesized topic order from schedule + exam prep + piazza FAQ across 3 sources. MEDIUM confidence noted. | Partially relevant | Accurate |
| 4 | What is the most common mistake students make with the pumping lemma? | Students treat p as their choice; adversary actually chooses p. Proof must work for ALL valid splits. | Retrieved correct chunk from cs301_topic_regular_languages.txt describing the adversary-chooses-p misconception. | Relevant | Accurate |
| 5 | What is this course about, when are the exams, and which TA sections are recommended? | Needs 3 sources: syllabus overview + exam schedule + lab/TA guide. | Retrieved mostly from syllabus (high similarity). Exam dates partially answered. TA section recommendations absent — that info not in top-5 chunks. | Partially relevant | Partially accurate |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:** "What is the subset construction algorithm and what is the worst-case number of states in the resulting DFA if the input NFA has n states?"
 
**What the system returned:** LOW confidence redirect — "There's no current verified information regarding your question about CS 301 in our database." No answer was generated despite the document `cs301_topic_dfa_nfa.txt` containing a detailed explanation of the algorithm.
 
**Root cause (tied to a specific pipeline stage):** The failure occurred at the **retrieval stage** due to a vocabulary mismatch between the query and the document. The query used the phrase "subset construction algorithm" but `cs301_topic_dfa_nfa.txt` primarily uses "NFA to DFA conversion" and "powerset construction" as its terminology. The embedding model `all-MiniLM-L6-v2` was trained on general web text and lacks knowledge of CS theory terminology equivalences — it could not bridge "subset construction" to "powerset construction" semantically. All returned chunks had cosine distances above 0.66, triggering the low-confidence fallback. This is a known limitation of using a general-purpose embedding model for a domain-specific technical corpus.
 
**What you would change to fix it:** Two approaches: (1) **Query-side synonym expansion** — before embedding, detect known CS theory terms and expand them (e.g., "subset construction" → "subset construction OR powerset construction OR NFA to DFA conversion"), then embed the expanded query. (2) **Document-side terminology alignment** — rewrite the document to include "subset construction algorithm" as an explicit term alongside existing phrasing, so the vocabulary gap disappears at the source. For a production system, approach (1) is more scalable; approach (2) is faster to implement for a known failure case.

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:**
Writing the chunking strategy in `planning.md` before coding forced an explicit decision about *why* paragraph-level splitting would fail for lecture content specifically. The reasoning — "a pumping lemma proof only makes sense as a complete unit: setup + example + key insight together" — directly shaped the type-aware dispatch in `ingest.py`. Without the spec, the implementation would likely have used a single fixed-character splitter and produced fragmented proof chunks. The spec also made it easy to direct Claude to implement `chunk_document()` correctly on the first attempt, because the boundary markers (`Q:`, `Topic:`, `\n\n`) and size constraints were already precisely defined.

**One way your implementation diverged from the spec, and why:**
The spec planned for the narrative document type (Type C) to cover only `cs301_instructor_profile.txt`. During implementation, `cs301_instructor_profile.txt` turned out to contain mostly exam prep content (final exam definitions and practice problem types) rather than a biographical profile — the document was generated with different content than the name implied. Rather than rename and re-register the file under deadline pressure, the narrative chunker was kept for that file but its practical function became exam prep rather than instructor biography. This is documented honestly as a naming mismatch: the file name implies profile content, but the chunking strategy applied (paragraph-level) still works well for the actual content structure.

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1**
 
- *What I gave the AI:* I discussed my idea for a TA-verified course information assistant RAG system with Claude, based on CS 301: Languages & Automata — a course I serve as Teaching Assistant for. I described the document types (syllabus, lecture content, homework-derived guides, Piazza FAQ), the three-way chunking strategy I was considering, the confidence tiering design based on cosine distance thresholds, and the contribution loop concept. I also shared recent CS Education research trends on course assistant RAG systems to contextualize the design against existing work and potential SIGCSE SRC directions.
- *What it produced:* Claude helped refine the raw idea into a structured system design with authority-level metadata, generated the architecture diagram, articulated the rationale for each chunking strategy decision, drafted the full `planning.md` and `README.md` skeleton, and produced all four pipeline files (`ingest.py`, `embed.py`, `query.py`, `app.py`).
- *What I changed or overrode:* I overrode the initial suggestion to use a single fixed-character chunking strategy for all document types — Claude's first proposal used 400-character fixed splitting uniformly. I pushed back because Q&A pairs and lecture proof units are semantically coherent units that must not be split mid-content, directing Claude to implement type-aware dispatch instead. I also added the confidence tiering feature (distance threshold → High/Medium/Low label surfaced in the UI) as my own design contribution after Claude flagged the epistemic transparency gap in existing course assistant systems. For the system prompt, I overrode Claude's soft initial draft ("use the provided context") with an explicit prohibition ("Answer ONLY using information from the retrieved documents. Do not use any outside knowledge") plus an explicit fallback instruction.
**Instance 2**
 
- *What I gave the AI:* After the pipeline was built, I gave Claude the actual `python query.py` terminal output showing the three retrieval test results — including the LOW confidence failure on "What is the subset construction algorithm?" with top distance 0.66 — and asked it to help me write the Failure Case Analysis and Retrieval Test Results sections of the README.
- *What it produced:* Claude drafted the failure case explanation attributing the failure to vocabulary mismatch at the retrieval stage, and drafted the two proposed fixes (query-side synonym expansion and document-side terminology alignment).
- *What I changed or overrode:* I verified the root cause diagnosis against my own understanding of how the embedding model works — the explanation was accurate. I kept the synonym expansion fix as the primary recommendation because it's more scalable, but added the document-side fix as the secondary option since it's faster to implement for a single known failure. I also corrected the distance scores in the retrieval results to match the actual terminal output (0.1837, 0.6638, 0.3766) rather than the rounded approximations Claude initially used.
