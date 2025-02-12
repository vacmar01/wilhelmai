from fasthtml.common import (
    Script,
    fast_app,
    Div,
    H1,
    P,
    Form,
    Input,
    serve,
    EventStream,
    Hidden,
    sse_message,
    NotStr,
    Span,
    A,
    H2,
)

import asyncio
import mistletoe
from dotenv import load_dotenv
from dataclasses import dataclass

from utils import (
    get_search_term,
    search_results,
    get_best_result,
    get_article_text,
    anthropic,
    setup_db,
)


load_dotenv()

c = setup_db("data/cache.db")


@dataclass
class Source:
    title: str
    url: str


async def answer_question(query: str):
    search_term = get_search_term(query)

    yield sse_message(
        Div(cls="m-2 text-zinc-400 animate-pulse")(
            f"Searching for '{search_term.text}'..."
        )
    )
    await asyncio.sleep(0.025)

    all_search_results = search_results(search_term, c)

    if len(all_search_results) == 0:
        yield sse_message(
            Div(cls="m-2 text-zinc-800")(
                f"Could not find any search results for '{search_term.text}'..."
            )
        )
        yield "event: close\ndata: \n\n"

    r = get_best_result(query, all_search_results)

    yield sse_message(
        Div(cls="m-2 text-zinc-400 animate-pulse")(
            f"Identified '{all_search_results[r.id]['title']}' as best search result..."
        )
    )
    await asyncio.sleep(0.025)
    assert r.id >= 0 and r.id <= 5

    article_text = get_article_text(
        f"https://radiopaedia.org{all_search_results[r.id]['href']}", c
    )

    source = Source(
        title=all_search_results[r.id]["title"],
        url=f"https://radiopaedia.org{all_search_results[r.id]['href']}",
    )

    prompt = f"""Answer the user query faithfully using the information in the context. 
    
    If you don't know the answer don't fabricate an answer, just say 'I don't know'. 
    
    Don't start your answer with something like 'Based on the context...'. Do not mention the context in your answer. This is very important Return the answer directly.
    
    context: {article_text}
    query: {query}"""

    with anthropic.messages.stream(
        model="claude-3-5-haiku-latest",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    ) as stream:
        result = ""
        for text in stream.text_stream:
            result += text
            yield sse_message(
                Div(id="content", cls="prose")(NotStr(mistletoe.markdown(result)))
            )
            await asyncio.sleep(0.025)
        yield sse_message(
            (
                Div(id="content", cls="prose")(NotStr(mistletoe.markdown(result))),
                SourceComponent(source),
            )
        )
        yield "event: close\ndata: \n\n"


twcss = Script(src="https://cdn.tailwindcss.com/?plugins=typography")
sse = Script(src="https://unpkg.com/htmx-ext-sse@2.2.2/sse.js")
app, rt = fast_app(
    pico=False,
    hdrs=(twcss, sse),
    live=True,
)


def SourceComponent(source: Source):
    return Div(cls="mt-4 text-xs text-gray-400")(
        Div(
            Span("Source", cls="block mb-1"),
            A(
                source.title,
                href=source.url,
                target="_blank",
                cls="rounded inline-block p-1 text-gray-800 bg-zinc-100 font-semibold",
            ),
        )
    )


def Question(qtext=""):
    return Div(
        qtext,
        cls="p-4 rounded text-lg font-semibold",
    )


def Answer(**kwargs):
    return Div(cls="bg-white border border-zinc-100 p-4 ")(
        Div("Answer", cls="text-zinc-400 text-sm mb-2"),
        Div(id="loading")(
            Script(
                code="document.body.addEventListener('htmx:sseBeforeMessage', e => {me('#loading').style.display = 'none'})"
            ),
            Div(cls="m-2 text-zinc-400 animate-pulse")("Thinking..."),
        ),
        Div(cls="text-zinc-800")(
            **kwargs,
        ),
    )


@rt
def ask(query: str):
    return Question(query), Answer(
        hx_ext="sse",
        sse_connect=receive_answer.to(query=query),
        sse_swap="message",
        sse_close="close",
        hx_swap="innerHTML",
    )


@rt
def receive_answer(query: str):
    return EventStream(answer_question(query))


@rt
def index():
    def ExampleQuestion(qtext=""):
        return Div(
            Form(hx_post=ask.to(), hx_target="#result", hx_trigger="click")(
                Hidden(name="query", value=qtext),
                qtext,
            ),
            cls="p-4 bg-zinc-100 rounded border border-zinc-200 cursor-pointer hover:opacity-70",
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

    return Div(cls="max-w-[600px] mx-auto p-4 max-h-screen flex flex-col")(
        H1(cls="text-3xl font-bold text-zinc-800 mb-4 text-center")("RadioSage"),
        Div(
            cls="space-y-2 p-2 text-zinc-800 bg-zinc-50 rounded flex-1 min-h-0 flex flex-col"
        )(
            Div(id="result", cls="rounded overflow-auto flex-1 min-h-0")(
                P(
                    "Ask any radiology related question below. RadioSage will try to answer it and give you a source for its answer.",
                    cls="text-lg text-zinc-400 text-center my-8",
                ),
                H2("Example Questions", cls="text-lg text-zinc-600 mb-2 font-semibold"),
                Div(cls="grid grid-cols-2 gap-2 text-zinc-600")(
                    *[
                        ExampleQuestion(
                            q,
                        )
                        for q in example_queries
                    ],
                ),
            ),
            Div(cls="shrink-0")(SubmitForm()),
        ),
    )


serve()
