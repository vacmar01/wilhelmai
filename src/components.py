from .lib import Source

from fasthtml.common import A, Div, NotStr, Script, Span, Br, Button, H1, Img, P, H2
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
                    href="/app",
                )(
                    Heroicon("cube-transparent", cls="text-green-500 w-6 h-6"),
                    H1(cls="text-2xl font-bold")(
                        "wilhelm",
                        Span(".ai", cls="text-green-500"),
                    ),
                )
            ),
            Div(cls="flex items-center")(
                A(href="/app")(
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
                    A(href="/app")(
                        Button(
                            cls="px-6 py-3 flex items-center gap-2 rounded-md font-medium text-white bg-green-500 hover:bg-green-600 transition-colors"
                        )(Heroicon("rocket-launch", cls="w-4"), "Let's get started")
                    ),
                ),
            ),
        ),
    )


def Features():
    def FeatureCard(icon, title, description):
        return Div(cls="text-center p-6")(
            Div(
                cls="mx-auto w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4"
            )(Heroicon(icon, cls="w-6 h-6 text-green-600")),
            H1(cls="text-lg font-semibold text-zinc-900 mb-2")(title),
            P(cls="text-gray-600")(description),
        )

    return Div(cls="py-16 bg-gray-50")(
        Div(cls="max-w-7xl mx-auto p-4")(
            Div(cls="text-center mb-16")(
                H1(cls="text-3xl font-bold text-zinc-900 mb-4")(
                    "Trusted Radiology Knowledge"
                ),
                P(cls="text-xl text-gray-600 max-w-2xl mx-auto")(
                    "Powered by Radiopaedia.org's comprehensive database of radiology cases and expert insights."
                ),
            ),
            Div(cls="grid md:grid-cols-3 gap-8")(
                FeatureCard(
                    "magnifying-glass",
                    "Instant Answers",
                    "Get immediate responses to your radiology questions with citations from authoritative sources.",
                ),
                FeatureCard(
                    "academic-cap",
                    "Educational Focus",
                    "Learn from detailed explanations and explore related cases to deepen your understanding.",
                ),
                FeatureCard(
                    "shield-check",
                    "Trusted Sources",
                    "All content sourced from Radiopaedia.org, ensuring reliable and peer-reviewed information.",
                ),
            ),
        )
    )


def ExampleQuestions():
    def QuestionExample(question):
        return A(
            href="/app",
            cls="block p-4 border border-gray-200 rounded-lg hover:border-green-300 transition-colors cursor-pointer",
        )(
            P(cls="text-gray-700 mb-2")(f'"{question}"'),
            Div(cls="flex items-center text-sm text-green-600")(
                Heroicon("arrow-right", cls="w-4 h-4 mr-1"), "Try this question"
            ),
        )

    return Div(cls="py-16 bg-white")(
        Div(cls="max-w-7xl mx-auto p-4")(
            Div(cls="text-center mb-12")(
                H1(cls="text-3xl font-bold text-zinc-900 mb-4")("Popular Questions"),
                P(cls="text-xl text-gray-600")(
                    "See what radiologists and students are asking"
                ),
            ),
            Div(cls="grid md:grid-cols-2 gap-6 max-w-4xl mx-auto")(
                QuestionExample(
                    "How do I differentiate between type 1 and type 2 endoleaks on CTA?"
                ),
                QuestionExample("What critical shoulder angle is normal?"),
                QuestionExample("How can I differentiate hepatic adenoma from FNH?"),
                QuestionExample(
                    "How do I classify hemorrhagic transformation of ischemic stroke?"
                ),
            ),
            Div(cls="text-center mt-8")(
                A(href="/app")(
                    Button(
                        cls="px-6 py-2 text-green-600 border border-green-600 rounded-md hover:bg-green-50 transition-colors"
                    )("Try it now")
                )
            ),
        )
    )


def CTA():
    return Div(cls="py-16 bg-green-600")(
        Div(cls="max-w-4xl mx-auto p-4 text-center")(
            H1(cls="text-3xl font-bold text-white mb-4")(
                "Ready to enhance your radiology knowledge?"
            ),
            P(cls="text-xl text-green-100 mb-8")(
                "Join radiologists and students who trust Wilhelm.ai for reliable answers."
            ),
            Div(cls="flex justify-center")(
                A(href="/app")(
                    Button(
                        cls="px-6 py-3 bg-white text-green-600 rounded-md font-medium hover:bg-gray-50 transition-colors"
                    )("Get Started For Free")
                )
            ),
        )
    )


def Footer():
    return Div(cls="bg-white border-t border-gray-200")(
        Div(cls="max-w-7xl mx-auto p-4 py-8")(
            Div(cls="flex flex-col md:flex-row justify-between items-center")(
                Div(cls="flex items-center mb-4 md:mb-0")(
                    Heroicon("cube-transparent", cls="text-green-500 w-6 h-6 mr-2"),
                    H1(cls="text-lg font-bold")(
                        "wilhelm",
                        Span(".ai", cls="text-green-500"),
                    ),
                ),
                P(cls="text-sm text-gray-500 text-center md:text-right")(
                    "Educational tool powered by Radiopaedia.org content. ",
                    Br(),
                    "Not intended for clinical use.",
                ),
            )
        )
    )
