import gradio as gr
from utils import answer_question

from db import add_query, initialize_database

def gr_answer_question(query):
    answer, source = answer_question(query)
    add_query(query, answer)
    return answer, source

demo = gr.Interface(
    title="🥼 rpAI",
    fn=gr_answer_question,
    inputs=gr.Textbox(label="Your Query", placeholder="Ask a radiology question here..."),
    outputs=[gr.Textbox(label="Answer", lines=5), gr.Textbox(label="Source")],
    examples=[
        "how to tell if disc infection or just degeneration",
        "pneumonitis",
        "How do I measure tibial tuberosity-trochlear groove (TT-TG) distance on CT?"
    ]
)


if __name__ == "__main__":
    initialize_database()
    demo.launch()