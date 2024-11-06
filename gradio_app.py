import gradio as gr
from utils import answer_question

from db import add_query, initialize_database

def gr_answer_question(query):
    try:
        answer, source = answer_question(query)
        add_query(query, answer)
    except Error as e:
        return "Error: No source found", ""
    return answer, source

demo = gr.Interface(
    title="🥼 rpAI",
    fn=gr_answer_question,
    inputs=gr.Textbox(label="Your Query", placeholder="Ask a radiology question here..."),
    outputs=[gr.Textbox(label="Answer", lines=5), gr.Textbox(label="Source", show_copy_button=True)],
    examples=[
        "pneumonitis",
        "How do I measure tibial tuberosity-trochlear groove (TT-TG) distance on CT?",
        "McDonald criteria",
        "tell me something about adem. what are the triggers and how does it look on MRI?"
    ]
)


if __name__ == "__main__":
    initialize_database()
    demo.launch(root_path="/radioprag")
