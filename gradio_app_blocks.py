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

with gr.Blocks(title="🥼 rpAI", css="""
    .main-container { gap: 20px; }
    .output-box { margin-top: 10px; }
""") as demo:
    gr.Markdown("# 🥼 rpAI")
    
    with gr.Row(elem_classes="main-container"):
        # Left column - Input
        with gr.Column(scale=1):
            question_input = gr.Textbox(
                label="Your Question",
                placeholder="Type your question here...",
                lines=1
            )
            with gr.Row():
                gr.ClearButton([question_input])
                submit_btn = gr.Button("Get Answer", variant="primary")

        # Right column - Outputs
        with gr.Column(scale=1):
            # Answer section
            gr.Markdown("### Answer")
            answer_output = gr.Markdown()
            
            # Sources section
            with gr.Column(elem_classes="output-box"):
                gr.Markdown("### Source")
                sources_output = gr.Textbox(
                    label="",
                    show_copy_button=True,
                    interactive=False,
                    lines=1
                )

    # Set up the function calls
    submit_btn.click(
        fn=gr_answer_question,
        inputs=question_input,
        outputs=[answer_output, sources_output],
        api_name="answer"
    )
    question_input.submit(
        fn=gr_answer_question,
        inputs=question_input,
        outputs=[answer_output, sources_output],
        api_name="answer_enter"
    )


if __name__ == "__main__":
    initialize_database()
    demo.launch(root_path="/radioprag")
