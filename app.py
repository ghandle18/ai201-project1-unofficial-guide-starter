"""
Milestone 5 - Gradio Web UI
Built with Claude and refined by me. Provides a user-friendly interface to ask questions and get TA-verified answers about CS 301 course policies, content, and exam prep. Displays confidence levels and sources to help students gauge reliability.
Due to time constraints, this UI focuses on core functionality and clarity, with a simple layout and essential features. Future iterations could add more interactivity, styling, and user feedback mechanisms.
app.py — Gradio web UI for the CS 301 Unofficial Course Assistant.

Run:  python app.py
Then: open http://localhost:7860
"""

import gradio as gr
from query import ask

CONFIDENCE_LABELS = {
    "high":   "✅ High confidence — answer drawn from verified course documents",
    "medium": "⚠️ Medium confidence — related information found; verify critical details with your TA",
    "low":    "❌ Low confidence — no verified information found; see answer for next steps",
}


def handle_query(question: str):
    if not question.strip():
        return "", "", "", ""

    result = ask(question.strip())

    confidence_label = CONFIDENCE_LABELS[result["confidence"]]
    sources = "\n".join(f"• {s}" for s in result["sources"]) if result["sources"] else "None"
    chunk_debug = "\n\n".join(
        f"[{c['source']} | authority: {c['authority']} | distance: {c['distance']}]\n"
        f"{c['text'][:300]}{'...' if len(c['text']) > 300 else ''}"
        for c in result["chunks"]
    )

    return result["answer"], confidence_label, sources, chunk_debug


with gr.Blocks(title="CS 301 Unofficial Guide", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 📚 CS 301: Languages & Automata — Unofficial Course Assistant
    ### TA-verified answers about course policies, content, and exam prep at UIC.
    *Answers are grounded in TA-curated documents — not general AI knowledge.*
    *When the system isn't sure, it tells you and points you to course staff.*
    """)

    with gr.Row():
        question_input = gr.Textbox(
            label="Your question",
            placeholder='e.g. "What is the late submission penalty?" or "How does subset construction work?"',
            lines=2,
        )

    ask_btn = gr.Button("Ask", variant="primary")

    with gr.Row():
        with gr.Column(scale=3):
            answer_output = gr.Textbox(label="Answer", lines=12)
        with gr.Column(scale=1):
            confidence_output = gr.Textbox(label="Confidence", lines=3)
            sources_output = gr.Textbox(label="Sources Used", lines=6)

    with gr.Accordion("Retrieved Chunks — debug view", open=False):
        chunks_output = gr.Textbox(label="Top Retrieved Chunks (with distances)", lines=20)

    gr.Examples(
        examples=[
            ["What is the late submission penalty for homework in CS 301?"],
            ["What is the subset construction algorithm and how many states can the result have?"],
            ["Which topics are weighted most heavily on CS 301 exams?"],
            ["What is the most common mistake students make with the pumping lemma?"],
            ["What is this course about, when are the exams, and which TA sections are recommended?"],
            ["What topics are covered in the DFA and NFA lecture?"],
            ["What should I know about the CS 301 lab sections?"],
        ],
        inputs=question_input,
    )

    ask_btn.click(
        handle_query,
        inputs=question_input,
        outputs=[answer_output, confidence_output, sources_output, chunks_output],
    )
    question_input.submit(
        handle_query,
        inputs=question_input,
        outputs=[answer_output, confidence_output, sources_output, chunks_output],
    )

if __name__ == "__main__":
    demo.launch()
