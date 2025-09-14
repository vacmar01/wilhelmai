from .lib import Source

from fasthtml.common import (
    A,
    Div,
    NotStr,
    Script,
)

import mistletoe


def SourceComponent(source: Source):
    return A(
        source.title,
        href=source.url,
        target="_blank",
        cls="rounded inline-block p-1 text-zinc-800 bg-zinc-100 font-semibold border border-zinc-200 hover:opacity-70",
    )


def QuestionComponent(qtext=""):
    return Div(
        qtext,
        cls="p-4 rounded text-lg font-semibold",
    )


def DocumentationComponent():
    return Div(cls="text-sm text-zinc-500 prose prose-zinc p-4 ")(
        NotStr(
            mistletoe.markdown("""This web app demonstrates the use of a large language model (LLM) combined with radiological information sourced from [Radiopaedia.org](https://radiopaedia.org) to answer radiology-related questions.

**Important disclaimer:**

- This tool is **not intended for clinical use** and should only be used for **demonstration, research, and educational purposes**.
- **Do NOT enter any patient data or any other sensitive information** into this application.
- All medical content is provided under the [Creative Commons Attribution-NonCommercial-ShareAlike 3.0 License](https://creativecommons.org/licenses/by-nc-sa/3.0/) from Radiopaedia.org.

Each generated answer provides a direct link to the original Radiopaedia.org source content for verification and further reference.
"""),
        )
    )


def AnswerComponent(*args, **kwargs):
    return Div(cls="bg-white border border-zinc-200 p-4 rounded")(
        Div("Answer", cls="text-zinc-400 text-sm mb-2"),
        Div(id="loading")(
            Script(
                "document.body.addEventListener('htmx:sseBeforeMessage', e => {me('#loading').remove()})"
            ),
            Div(cls="my-2 text-zinc-400 animate-pulse")("Thinking..."),
        ),
        Div(cls="text-zinc-800")(
            *args,
            **kwargs,
        ),
    )
