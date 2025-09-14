from .lib import Source

from fasthtml.common import A, Div, NotStr, Script, Span, Br, Button, H1, Img, P
from fh_heroicons import Heroicon

import mistletoe

bg_style = """background-color: #ffffff; background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100' height='100' viewBox='0 0 100 100'%3E%3Cg fill-rule='evenodd'%3E%3Cg fill='%2327272a' fill-opacity='0.05'%3E%3Cpath opacity='.5' d='M96 95h4v1h-4v4h-1v-4h-9v4h-1v-4h-9v4h-1v-4h-9v4h-1v-4h-9v4h-1v-4h-9v4h-1v-4h-9v4h-1v-4h-9v4h-1v-4h-9v4h-1v-4H0v-1h15v-9H0v-1h15v-9H0v-1h15v-9H0v-1h15v-9H0v-1h15v-9H0v-1h15v-9H0v-1h15v-9H0v-1h15v-9H0v-1h15v-9H0v-1h15V0h1v15h9V0h1v15h9V0h1v15h9V0h1v15h9V0h1v15h9V0h1v15h9V0h1v15h9V0h1v15h9V0h1v15h4v1h-4v9h4v1h-4v9h4v1h-4v9h4v1h-4v9h4v1h-4v9h4v1h-4v9h4v1h-4v9zm-1 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-9-10h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm9-10v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-9-10h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm9-10v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-9-10h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm9-10v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-9-10h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9z'/%3E%3Cpath d='M6 5V0H5v5H0v1h5v94h1V6h94V5H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");"""


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


def Navbar():
    return Div(cls="border-b border-gray-200 bg-white shadow-sm")(
        Div(
            cls="max-w-7xl h-16 flex mx-auto items-center justify-between px-4 sm:px-6"
        )(
            Div(cls="flex items-center")(
                A(
                    cls="hover:opacity-70 transition-opacity flex items-center gap-2",
                    href="/",
                )(
                    Heroicon("cube-transparent", cls="text-green-500 w-6 h-6"),
                    H1(cls="text-2xl font-bold")(
                        "wilhelm",
                        Span(".ai", cls="text-green-500"),
                    ),
                )
            ),
            Div(cls="flex items-center")(
                A(
                    cls="text-zinc-600 hover:text-zinc-900 flex font-medium items-center gap-1.5 transition-colors",
                    href="#",
                )(Heroicon("information-circle", cls="w-4"), "About")
            ),
            Div(cls="flex items-center")(
                A(href="/")(
                    Button(
                        cls="px-3 py-1.5 text-sm font-medium border rounded-md flex gap-2 items-center hover:bg-zinc-50 transition-color"
                    )("Go To App", Heroicon("arrow-top-right-on-square", cls="w-4"))
                )
            ),
        )
    )


def Hero():
    return Div(cls="max-w-7xl mx-auto p-4")(
        Div(cls="py-24 max-w-4xl mx-auto text-center relative")(
            Div(cls="absolute inset-0 opacity-5")(
                Img(
                    src="assets/roentgen_sketch.svg",
                    cls="w-full h-full object-contain",
                ),
            ),
            Div(cls="relative space-y-4")(
                Div(
                    cls="inline-block px-4 py-1.5 mb-8 text-sm font-medium bg-blue-50 text-blue-700 rounded-full"
                )("Revolutionizing Radiology Education"),
                H1(
                    cls="text-4xl sm:text-5xl md:text-6xl font-bold text-zinc-900 mb-6 leading-tight"
                )("Radiology Knowledge.", Br(), "At Your Fingertips"),
                P(cls="text-xl text-gray-600 mb-12 max-w-2xl mx-auto")(
                    "Wilhelm.ai finds and summarizes authoritative Radiopaedia content to answer your questions — fast, transparent, and educational."
                ),
                Div(cls="flex justify-center")(
                    A(href="/")(
                        Button(
                            cls="px-6 py-3 flex items-center gap-2 rounded-md font-medium text-white bg-green-500 hover:bg-green-600 transition-colors"
                        )(Heroicon("rocket-launch", cls="w-4"), "Let's get started")
                    ),
                ),
            ),
        ),
    )
