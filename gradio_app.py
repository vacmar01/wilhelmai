import gradio as gr
from utils import answer_question

from db import add_query, initialize_database

def gr_answer_question(query):
    generator = answer_question(query)
    # first_tuple = next(generator)  # Get first tuple to extract source
    # answer, _ = first_tuple
    # add_query(query, answer)
    # yield first_tuple  # Yield first tuple we already got
    for item in generator:  # Continue yielding remaining items
        yield item

demo = gr.Interface(
    title="🥼 rpAI",
    fn=answer_question,
    inputs=gr.Textbox(label="Your Query", placeholder="Ask a radiology question here..."),
    outputs=[gr.Textbox(label="Answer", lines=5), gr.Textbox(label="Source", show_copy_button=True)],
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

    # demo.queue()
    demo.launch()