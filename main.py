from fasthtml.common import (
    Script,
    fast_app,
    Div,
    H1,
    P,
    Meta,
    Form,
    Input,
    serve,
    EventStream,
    Dialog,
    Button,
    Hidden,
    Title,
    sse_message,
    NotStr,
    Span,
    A,
    Link,
    H2,
    HttpHeader,
)


import asyncio
import mistletoe
from dotenv import load_dotenv
from dataclasses import dataclass
from fh_heroicons import Heroicon
from claudette import Chat

from lib import (
    get_search_term,
    search_results,
    get_best_result,
    get_article_text,
    setup_db,
    create_chat,
)


load_dotenv()

c = setup_db("data/cache.db")


@dataclass
class Source:
    title: str
    url: str


async def stream_response(content: str, chat: Chat, source: Source = None):
    """Helper to stream markdown responses with optional source."""
    result = ""
    for text in chat(content, stream=True):
        result += text
        yield sse_message(
            Div(id="content", cls="prose")(NotStr(mistletoe.markdown(result)))
        )
        await asyncio.sleep(0.025)

    if source:
        yield sse_message(
            (
                Div(id="content", cls="prose")(NotStr(mistletoe.markdown(result))),
                SourceComponent(source),
            )
        )
    yield "event: close\ndata: \n\n"


async def answer_query(query: str, chat: Chat, search: bool = True):
    """Main coroutine to search and answer questions."""
    # Simple query - no search needed
    if not search:  # You'll need to implement this
        async for msg in stream_response(query, chat):
            yield msg
        return

    # Search flow
    term = get_search_term(query)
    yield sse_message(
        Div(cls="my-2 text-zinc-400 animate-pulse")(f"Searching for '{term.text}'...")
    )
    await asyncio.sleep(0.025)

    results = search_results(term, c)
    if not results:
        yield sse_message(
            Div(cls="my-2 text-zinc-800")(f"No results found for '{term.text}'...")
        )
        yield "event: close\ndata: \n\n"
        return

    best = get_best_result(query, results)
    yield sse_message(
        Div(cls="my-2 text-zinc-400 animate-pulse")(
            f"Found best match: '{results[best.id]['title']}'..."
        )
    )
    await asyncio.sleep(0.025)

    url = f"https://radiopaedia.org{results[best.id]['href']}"
    article = get_article_text(url, c)
    source = Source(title=results[best.id]["title"], url=url)
    prompt = f"<context>{article}</context>\n\n<query>{query}</query>"

    async for msg in stream_response(prompt, chat, source):
        yield msg


bg_style = """background-color: #ffffff; background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100' height='100' viewBox='0 0 100 100'%3E%3Cg fill-rule='evenodd'%3E%3Cg fill='%2327272a' fill-opacity='0.05'%3E%3Cpath opacity='.5' d='M96 95h4v1h-4v4h-1v-4h-9v4h-1v-4h-9v4h-1v-4h-9v4h-1v-4h-9v4h-1v-4h-9v4h-1v-4h-9v4h-1v-4h-9v4h-1v-4h-9v4h-1v-4H0v-1h15v-9H0v-1h15v-9H0v-1h15v-9H0v-1h15v-9H0v-1h15v-9H0v-1h15v-9H0v-1h15v-9H0v-1h15v-9H0v-1h15V0h1v15h9V0h1v15h9V0h1v15h9V0h1v15h9V0h1v15h9V0h1v15h9V0h1v15h9V0h1v15h9V0h1v15h4v1h-4v9h4v1h-4v9h4v1h-4v9h4v1h-4v9h4v1h-4v9h4v1h-4v9h4v1h-4v9h4v1h-4v9zm-1 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-9-10h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm9-10v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-9-10h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm9-10v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-9-10h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm9-10v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-9-10h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9z'/%3E%3Cpath d='M6 5V0H5v5H0v1h5v94h1V6h94V5H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");"""

fonts = (
    Link(rel="preconnect", href="https://fonts.googleapis.com"),
    Link(rel="preconnect", href="https://fonts.gstatic.com", crossorigin=""),
    Link(
        href="https://fonts.googleapis.com/css2?family=Geist:wght@100..900&display=swap",
        rel="stylesheet",
    ),
)

meta_tags = (
    Meta(name="description", content="RadRAG - Radiology Decision Support"),
    Meta(property="og:title", content="RadRAG - Radiology Decision Support"),
    Meta(property="og:description", content="RadRAG - Radiology Decision Support"),
    Meta(property="og:url", content="https://radrag-production.up.railway.app/"),
    Meta(property="og:type", content="website"),
    Meta(name="twitter:card", content="summary"),
    Meta(name="twitter:title", content="RadRAG - Radiology Decision Support"),
    Meta(name="twitter:description", content="RadRAG - Radiology Decision Support"),
)

twcss = Script(src="https://cdn.tailwindcss.com/?plugins=typography")
sse = Script(src="https://unpkg.com/htmx-ext-sse@2.2.2/sse.js")
app, rt = fast_app(
    pico=False,
    hdrs=(twcss, sse, *fonts, *meta_tags),
    live=True,
    bodykw={"style": bg_style + "font-family: 'Geist', sans-serif;"},
)


def SourceComponent(source: Source):
    return Div(cls="mt-4 text-xs text-zinc-400")(
        Div(
            Span("Source", cls="block mb-1"),
            A(
                source.title,
                href=source.url,
                target="_blank",
                cls="rounded inline-block p-1 text-zinc-800 bg-zinc-100 font-semibold border border-zinc-200 hover:opacity-70",
            ),
        )
    )


def QuestionComponent(qtext=""):
    return Div(
        qtext,
        cls="p-4 rounded text-lg font-semibold",
    )


def DocumentationComponent():
    return (
        Div(cls="text-sm text-zinc-500 prose prose-zinc")(
            H2(
                "What is this?",
            ),
            P(
                "RadRAG is an experiment by Dr. Marius Vach. It uses a large language model as well as radiological sources to answer radiology-associated questions. "
            ),
            P(
                "It's not meant to be for clinical use, but solely for demonstration purposes. "
            ),
            P("Do NOT enter any patient data or any other sensitive information."),
        ),
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


@rt
def index():
    chat = create_chat()

    @rt
    def ask(query: str):
        is_fu = bool(chat.h)
        response = (
            QuestionComponent(query),
            AnswerComponent(
                hx_ext="sse",
                sse_connect=receive_answer.to(query=query, search=not is_fu),
                sse_swap="message",
                sse_close="close",
                hx_swap="innerHTML show:bottom",
            ),
        )

        if is_fu:
            return (HttpHeader("HX-Reswap", "beforeend"),) + response
        return response

    @rt
    def receive_answer(query: str, search: bool = False):
        return EventStream(answer_query(query, chat, search=search))

    def ExampleQuestion(qtext=""):
        return Div(
            Form(hx_post=ask.to(), hx_target="#result", hx_trigger="click")(
                Hidden(name="query", value=qtext),
                qtext,
            ),
            cls="p-4 bg-white rounded border border-zinc-200 cursor-pointer hover:opacity-70",
        )

    example_queries = [
        "How to differentiate radiation necrosis from tumor progression on MRI?",
        "How does blood look like on MRI?",
        "What defines the UIP pattern?",
        "What is the ECASS classification?",
    ]

    def SubmitForm():
        return Form(
            hx_post=ask.to(),
            hx_target="#result",
            hx_swap="innerHTML",
            cls="flex gap-2 mt-4 border-t border-t-zinc-200 pt-4",
            **{"hx-on::after-request": "this.reset()"},
        )(
            Input(
                type="text",
                name="query",
                placeholder="Ask here ...",
                cls="border rounded border-zinc-200 p-2 bg-white flex-1",
            ),
        )

    return Title("RadRAG"), Div(
        cls="max-w-[600px] mx-auto p-4 max-h-screen flex flex-col"
    )(
        Div(cls="flex justify-between items-center mb-4")(
            H1(cls="text-3xl font-bold text-zinc-800 flex gap-2 items-center")(
                Heroicon("cube-transparent", cls="text-green-500 w-6 h-6"),
                A(href="/")("RadRAG"),
            ),
            Button(
                Heroicon("information-circle", cls="w-6 h-6 text-zinc-800"),
                Script("me().on('click', () => me('#info-modal').showModal())"),
                cls="hover:opacity-70",
            ),
            A(
                href="/",
                cls="flex gap-2 border border-zinc-200 bg-zinc-100 text-zinc-800 p-2 rounded font-semibold hover:opacity-70",
            )(Heroicon("plus", cls="w-6 h-6"), "New Chat"),
        ),
        Dialog(
            id="info-modal",
            cls="p-2 max-w-sm bg-zinc-100 border rounded border-zinc-200",
        )(
            Button(
                Heroicon("x-mark"),
                Script("me().on('click', () => me('#info-modal').close())"),
                cls="absolute top-2 right-2 cursor-pointer",
            ),
            DocumentationComponent(),
        ),
        Div(
            cls="space-y-2 p-2 text-zinc-800 bg-zinc-100 border border-zinc-200 rounded flex-1 min-h-0 flex flex-col"
        )(
            Div(id="result", cls="rounded overflow-auto flex-1 min-h-0")(
                P(
                    "Ask any radiology related question below. RadRAG will try to answer it and give you a source for its answer.",
                    cls="text-zinc-400 text-center my-8",
                ),
                H2("Example Questions", cls="text-lg text-zinc-800 mb-2 font-semibold"),
                Div(cls="grid grid-cols-2 gap-2 text-zinc-800")(
                    *[ExampleQuestion(q) for q in example_queries],
                ),
            ),
            Div(cls="shrink-0")(SubmitForm()),
        ),
    )


serve()
