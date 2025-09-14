import asyncio
import mistletoe
import logging

from .lib import (
    LogicEvent,
    SearchEvent,
    FoundArticleEvent,
    ErrorEvent,
    StopEvent,
    AnswerChunkEvent,
    FinalAnswerEvent,
    SourcesEvent,
    aanswer_query,
    ConversationManager,
)

from .components import SourceComponent

from fasthtml.common import Div, Span, NotStr, sse_message


def event_to_sse(event: LogicEvent):
    match event:
        case AnswerChunkEvent(answer) | FinalAnswerEvent(answer):
            return sse_message(
                Div(id="content", cls="prose")(NotStr(mistletoe.markdown(answer)))
            )
        case SourcesEvent(sources, answer):
            return sse_message(
                (
                    Div(id="content", cls="prose")(NotStr(mistletoe.markdown(answer))),
                    Div(cls="mt-4 text-xs text-zinc-400")(
                        Div(
                            Span("Sources", cls="block mb-1"),
                            Div(cls="flex flex-wrap gap-2")(
                                *[SourceComponent(source) for source in sources],
                            ),
                        )
                    ),
                )
            )
        case SearchEvent(terms):
            return sse_message(
                Div(cls="my-2 text-zinc-400 animate-pulse")(
                    f"Searching for '{', '.join(terms)}'..."
                )
            )
        case FoundArticleEvent(term):
            return sse_message(
                Div(cls="my-2 text-zinc-400 animate-pulse")(
                    f"Found best match for '{term}'"
                )
            )
        case ErrorEvent(message):
            return sse_message(Div(cls="my-2 text-zinc-800")(message))
        case StopEvent():
            return "event: close\ndata: \n\n"


async def answer_query_sse(query: str, conv_id: str, conversation_manager: ConversationManager):
    """This function consumes the events from the answer_query generator and yields SSE messages with HTML in it."""
    start_time = asyncio.get_event_loop().time()

    _, history = conversation_manager.get_or_create_conversation(conv_id)

    async for event in aanswer_query(query, history):
        yield event_to_sse(event)
        if isinstance(event, FinalAnswerEvent):
            history.messages.append(
                {
                    "user_query": query,
                    "answer": event.answer,
                    "articles": event.articles,
                }
            )
            conversation_manager.update_conversation(conv_id, history)
        if isinstance(event, StopEvent):
            end_time = asyncio.get_event_loop().time()
            logging.info(f"answered query in {end_time - start_time:.2f} seconds")
            return


