from anthropic import AsyncAnthropic
from dotenv import load_dotenv
import logging
import httpx
from bs4 import BeautifulSoup
import apsw
import apsw.bestpractice

from openai import AsyncOpenAI, OpenAI
import asyncio
from dataclasses import dataclass

import os
import re

load_dotenv()


class ConversationManager:
    def __init__(self):
        sp = """You are an **Information Extractor Bot**. Your *only* function is to extract answers from a provided text context that directly correspond to a user's query.

**Core Rules:**

1.  **Context is Everything:** You MUST base your response *entirely* on the provided context document.
2.  **Sufficiency Check:** First, determine if the context contains the necessary information to answer the query.
3.  **Handling Insufficient Context:** If the context does not contain the answer, you MUST respond with the exact phrase: "The provided context does not contain the information to answer this query." Nothing more.
4.  **Generating the Answer (If Context Allows):** If the context *does* contain the answer:
    *   Extract the relevant information.
    *   Format it using markdown for readability and high educational value.
    *   Use headings within the answer body if appropriate, but **do not** start the answer with a heading.
    *   Present the extracted answer directly, without mentioning the context source.
    *   Keep the answer concise and relevant to the query.

**ABSOLUTE PROHIBITION:** Do not access or use any external knowledge, training data, or general information. Your knowledge is strictly limited to the context provided for each query. Failure to find the answer in the context requires the specific failure message above."""
        self.msgs = [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": sp,
                    }
                ],
            }
        ]  # Initialize the message list here

    def add_user_message(self, content):
        self.msgs.append({"role": "user", "content": content})

    def add_assistant_message(self, content):
        self.msgs.append({"role": "assistant", "content": content})

    def get_messages(self):
        return self.msgs

    def clear_messages(self):
        self.msgs = []


@dataclass
class Source:
    title: str
    url: str


@dataclass
class AnswerChunkEvent:
    chunk: str


@dataclass
class SourcesEvent:
    sources: list[Source]
    answer: str


@dataclass
class SearchEvent:
    terms: list[str]


@dataclass
class FoundArticleEvent:
    term: str


@dataclass
class ErrorEvent:
    term: str
    error: str


@dataclass
class StopEvent:
    pass


LogicEvent = (
    AnswerChunkEvent
    | SearchEvent
    | FoundArticleEvent
    | ErrorEvent
    | SourcesEvent
    | StopEvent
)


ANTHROPIC_MODEL = "claude-3-5-haiku-latest"


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    # filename='app.log'  # Remove this line to log to console instead
)

http_headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "accept-language": "de-DE,de;q=0.7",
    "cache-control": "max-age=0",
    "cookie": "*radiopaedia*session=FK2kLR8%2Bhkzg8D5gtP4N4x7y7QoL55kFD40yMiPSOY7%2FN2z7QD85jgYgOl36adv2O4KM%2Buk9%2BIxtFUDX3LTHoSSOeoykDZyd%2FLqq5OPox0tzbn1URW4n5oZhowZCpw9MHPRvZ%2FAIDDhAtaJxz7Ue3hBb%2BjcKRloPcYbUjUBOi4KvtINrFnKpfey%2B13AgAz8bcuzLURQiO07IXbnVRackkRXpgG0mBcjh8n1Ap849t33s81SgYXTXFGeBit4JVhTtqLGrUa%2F%2FIXFZZyKREUk9b8kQYmvUIRtE9Fmr1Rd43JQOa60hTs%2F4Vhh%2F1rClz1pAgZrzAIEDbzx%2Bvz1CKDU%2FhHlydPYIcvrhZXOQ6TKhRDV8bfrfKjjToXAH9vyFbq4VxlnAnyoCA4JBFetkzZbrqrZSYsM%2F%2BF7LW8Swh92pLtO%2BwAps555wlyXnQKDbrapf%2FNaABd3%2Bk301t64uwC1n4nkq3Z7rIG409N%2FFfzylkrNs1eOArX1j%2FqkilucHBXMt--A7TmaE8Ut8M5kXCo--txKn9l3AgN8d8znLnEjAKw%3D%3D",
    "priority": "u=0, i",
    "sec-ch-ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Brave";v="128"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "sec-gpc": "1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
}


def extract_all_query_content(text: str) -> list[str]:
    # Extract content between search_terms tags
    search_terms_match = re.search(
        r"<search_terms>(.*?)</search_terms>", text, re.DOTALL
    )
    if not search_terms_match:
        return []

    # Get the content and split by lines
    search_terms_content = search_terms_match.group(1).strip()
    search_terms = [
        term.strip() for term in search_terms_content.splitlines() if term.strip()
    ]

    return search_terms


async def aget_search_terms(query: str) -> list[str]:
    client = AsyncOpenAI(
        base_url="https://api.together.xyz/v1",
        api_key=os.getenv("TOGETHER_API_KEY"),
    )
    model = "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"

    # message = await client.messages.create(
    #     model=ANTHROPIC_MODEL,
    #     max_tokens=8192,
    #     temperature=0.2,
    #     messages=[
    #         {
    #             "role": "user",
    #             "content": [
    #                 {
    #                     "type": "text",
    #                     "text": '<examples>\n<example>\n<query>\nWhat are the findings of acute pancreatitis on contrast-enhanced CT?\n</query>\n<ideal_output>\n<analysis>\n1. Main radiological concept: acute pancreatitis\n2. The query does not require a comparison or multiple distinct concepts.\n3. The most appropriate technical term is "acute pancreatitis".\n4. This search term is justified because it directly addresses the main concept in the query. Although the query asks about the cause, searching for "acute pancreatitis" will likely provide information about its etiology, including the most common cause.\n</analysis>\n<search_terms>acute pancreatitis</search_terms>\n</ideal_output>\n</example>\n<example>\n<query>\nWhat is the MTA score?\n</query>\n<ideal_output>\n<analysis>\n1. Main radiological concept: MTA score\n2. The query does not require a comparison or multiple distinct concepts.\n3. The most appropriate technical term is "MTA score".\n4. This search term is justified because it directly addresses the main concept in the query. While the query asks about a specific age and pathological score, searching for "MTA score" will likely provide comprehensive information about the scoring system, including age-related norms and pathological thresholds.\n</analysis>\n<search_terms>MTA score</search_terms>\n</ideal_output>\n</example>\n<example>\n<query>\nHow to differentiate radiation necrosis from tumor recurrence on MRI?\n</query>\n<ideal_output>\n<analysis>\n1. Main radiological concepts: radiation necrosis, tumor recurrence\n2. The query implies a comparison between two conditions, but does not explicitly ask for both to be searched.\n3. The most appropriate technical term is "radiation necrosis".\n4. This search term is justified because it focuses on one of the main concepts in the query. While the question involves differentiating between radiation necrosis and tumor recurrence, searching for "radiation necrosis" will likely provide information on its characteristics and how to distinguish it from tumor recurrence. As per the guidelines, we provide only one search term unless explicitly asked for multiple terms.\n</analysis>\n<search_terms>radiation necrosis</search_terms>\n</ideal_output>\n</example>\n<example>\n<query>\nHow to differentiate primary CNS lymphoma from glioblastoma on MRI?\n</query>\n<ideal_output>\n<analysis>\n1. Main radiological concepts: primary CNS lymphoma, glioblastoma\n2. The query explicitly asks for a comparison between two conditions.\n3. The most appropriate technical terms are "CNS lymphoma" and "glioblastoma".\n4. These search terms are justified because the query specifically asks for a comparison between these two conditions. As per the guidelines, we provide multiple search terms when the query explicitly requires a comparison.\n</analysis>\n<search_terms>CNS lymphoma\nglioblastoma</search_terms>\n</ideal_output>\n</example>\n<example>\n<query>\nHow does a TOF MRA work?\n</query>\n<ideal_output>\n<analysis>\n1. Main radiological concept: TOF MRA (Time-of-Flight Magnetic Resonance Angiography)\n2. The query does not require a comparison or multiple distinct concepts.\n3. The most appropriate technical term is "TOF MRA".\n4. This search term is justified because it directly addresses the main concept in the query. While the question asks about the working principle, searching for "TOF MRA" will likely provide comprehensive information about the technique, including how it works.\n</analysis>\n<search_terms>TOF MRA</search_terms>\n</ideal_output>\n</example>\n<example>\n<query>\nWhat\'s chemical shift imaging?\n</query>\n<ideal_output>\n<analysis>\n1. Main radiological concept: chemical shift imaging\n2. The query does not require a comparison or multiple distinct concepts.\n3. The most appropriate technical term is "chemical shift imaging".\n4. This search term is justified because it directly matches the concept asked about in the query. It is a concise noun phrase that captures the specific imaging technique in question.\n</analysis>\n<search_terms>chemical shift imaging</search_terms>\n</ideal_output>\n</example>\n</examples>\n\n',
    #                 },
    #                 {
    #                     "type": "text",
    #                     "text": f"You are an experienced radiologist tasked with generating relevant search terms for Radiopaedia based on user queries about radiological topics. Your goal is to identify the core concept(s) or condition(s) mentioned in the query and provide concise, targeted search terms.\n\nHere is the user's query:\n\n<user_query>\n{query}\n</user_query>\n\nPlease analyze the query and determine the most appropriate search term(s). Follow these guidelines:\n\n1. Identify the main radiological concept, condition, or imaging technique mentioned in the query.\n2. If the query explicitly asks for a comparison between two conditions or concepts, provide search terms for both.\n3. In most cases, provide only one search term unless the query specifically demands multiple terms.\n4. Search terms should be concise noun phrases or technical terms, not full questions.\n5. Focus on the underlying medical concept, even if the query is about a specific aspect of that concept.\n\nBefore providing your final output, wrap your analysis in <analysis> tags. In this analysis:\n\n1. List the main radiological concepts or conditions mentioned in the query.\n2. Determine if the query requires a comparison or multiple distinct concepts.\n3. Consider the most appropriate technical term or concise noun phrase for each identified concept.\n4. Justify your choice of search term(s) based on the guidelines provided.\n\nAfter your analysis, provide the search term(s) in the following format:\n\n<search_terms>\n[One search term per line]\n</search_terms>\n\nRemember to only include multiple search terms if the query explicitly requires a comparison or multiple distinct concepts.",
    #                 },
    #             ],
    #         },
    #         {"role": "assistant", "content": [{"type": "text", "text": "<analysis>"}]},
    #     ],
    # )

    message = await client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": '<examples>\n<example>\n<query>\nWhat are the findings of acute pancreatitis on contrast-enhanced CT?\n</query>\n<ideal_output>\n<analysis>\n1. Main radiological concept: acute pancreatitis\n2. The query does not require a comparison or multiple distinct concepts.\n3. The most appropriate technical term is "acute pancreatitis".\n4. This search term is justified because it directly addresses the main concept in the query. Although the query asks about the cause, searching for "acute pancreatitis" will likely provide information about its etiology, including the most common cause.\n</analysis>\n<search_terms>acute pancreatitis</search_terms>\n</ideal_output>\n</example>\n<example>\n<query>\nWhat is the MTA score?\n</query>\n<ideal_output>\n<analysis>\n1. Main radiological concept: MTA score\n2. The query does not require a comparison or multiple distinct concepts.\n3. The most appropriate technical term is "MTA score".\n4. This search term is justified because it directly addresses the main concept in the query. While the query asks about a specific age and pathological score, searching for "MTA score" will likely provide comprehensive information about the scoring system, including age-related norms and pathological thresholds.\n</analysis>\n<search_terms>MTA score</search_terms>\n</ideal_output>\n</example>\n<example>\n<query>\nHow to differentiate radiation necrosis from tumor recurrence on MRI?\n</query>\n<ideal_output>\n<analysis>\n1. Main radiological concepts: radiation necrosis, tumor recurrence\n2. The query implies a comparison between two conditions, but does not explicitly ask for both to be searched.\n3. The most appropriate technical term is "radiation necrosis".\n4. This search term is justified because it focuses on one of the main concepts in the query. While the question involves differentiating between radiation necrosis and tumor recurrence, searching for "radiation necrosis" will likely provide information on its characteristics and how to distinguish it from tumor recurrence. As per the guidelines, we provide only one search term unless explicitly asked for multiple terms.\n</analysis>\n<search_terms>radiation necrosis</search_terms>\n</ideal_output>\n</example>\n<example>\n<query>\nHow to differentiate primary CNS lymphoma from glioblastoma on MRI?\n</query>\n<ideal_output>\n<analysis>\n1. Main radiological concepts: primary CNS lymphoma, glioblastoma\n2. The query explicitly asks for a comparison between two conditions.\n3. The most appropriate technical terms are "CNS lymphoma" and "glioblastoma".\n4. These search terms are justified because the query specifically asks for a comparison between these two conditions. As per the guidelines, we provide multiple search terms when the query explicitly requires a comparison.\n</analysis>\n<search_terms>CNS lymphoma\nglioblastoma</search_terms>\n</ideal_output>\n</example>\n<example>\n<query>\nHow does a TOF MRA work?\n</query>\n<ideal_output>\n<analysis>\n1. Main radiological concept: TOF MRA (Time-of-Flight Magnetic Resonance Angiography)\n2. The query does not require a comparison or multiple distinct concepts.\n3. The most appropriate technical term is "TOF MRA".\n4. This search term is justified because it directly addresses the main concept in the query. While the question asks about the working principle, searching for "TOF MRA" will likely provide comprehensive information about the technique, including how it works.\n</analysis>\n<search_terms>TOF MRA</search_terms>\n</ideal_output>\n</example>\n<example>\n<query>\nWhat\'s chemical shift imaging?\n</query>\n<ideal_output>\n<analysis>\n1. Main radiological concept: chemical shift imaging\n2. The query does not require a comparison or multiple distinct concepts.\n3. The most appropriate technical term is "chemical shift imaging".\n4. This search term is justified because it directly matches the concept asked about in the query. It is a concise noun phrase that captures the specific imaging technique in question.\n</analysis>\n<search_terms>chemical shift imaging</search_terms>\n</ideal_output>\n</example>\n</examples>\n\n',
                    },
                    {
                        "type": "text",
                        "text": f"<query>{query}</query>",
                    },
                ],
            },
            {"role": "assistant", "content": [{"type": "text", "text": "<analysis>"}]},
        ],
        temperature=0.2,
    )

    search_terms = extract_all_query_content(message.choices[0].message.content)

    logging.info(f"Searchterms for query: '{query}' are: '{search_terms}'")
    return search_terms


def structure_search_result(result, idx):
    return {
        "id": idx,
        "title": result.find(class_="search-result-title").text.strip(),
        "body": result.find(class_="search-result-body").text.strip(),
        "href": result["href"],
    }


def get_docs(search_results):
    return [d["title"] + " " + d["body"] for d in search_results]


async def asearch_results(search_term: str, cursor):
    soup = await asearch_radiopaedia(search_term, cursor)

    all_search_results = [
        structure_search_result(search_result, i)
        for i, search_result in enumerate(soup.find_all(class_="search-result"))
    ]

    return all_search_results


def setup_db(db_path=":memory:"):
    apsw.bestpractice.apply(apsw.bestpractice.recommended)
    connection = apsw.Connection(db_path)
    cursor = connection.cursor()
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS radiopaedia_search_results (search_query TEXT PRIMARY KEY, search_results TEXT)"
    )
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS radiopaedia_articles (url TEXT PRIMARY KEY, content TEXT)"
    )
    return cursor


async def aget_article_text(url, cursor):
    cache_hits = cursor.execute(
        "SELECT content FROM radiopaedia_articles WHERE url = ?", (url,)
    ).fetchall()
    if cache_hits:
        logging.info(f"Cache hit for url: '{url}'")
        return cache_hits[0][0]
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=http_headers)
    soup = BeautifulSoup(response.content, "html.parser")
    content = soup.select("#content > div.body.user-generated-content")[0].text.strip()
    cursor.execute(
        "INSERT INTO radiopaedia_articles (url, content) VALUES (?, ?)", (url, content)
    )
    return content


async def asearch_radiopaedia(search_query: str, cursor):
    url = "https://radiopaedia.org/search"
    cache_hits = cursor.execute(
        "SELECT search_results FROM radiopaedia_search_results WHERE search_query = ?",
        (search_query,),
    ).fetchall()
    if cache_hits:
        logging.info(f"Cache hit for search query: '{search_query}'")
        rbody = cache_hits[0][0]
        return BeautifulSoup(rbody, "html.parser")

    params = {"lang": "us", "q": search_query, "scope": "articles"}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, headers=http_headers)

    cursor.execute(
        "INSERT INTO radiopaedia_search_results (search_query, search_results) VALUES (?, ?)",
        (search_query, response.content),
    )

    return BeautifulSoup(response.content, "html.parser")


async def aprocess_term(term: str, c) -> tuple[list[str], list[Source]]:
    # Get search results for the term
    results = await asearch_results(term, c)
    if not results or len(results) == 0:
        # Return empty lists to indicate no results for this term
        return [], []

    # Take the top two results (or one if that's all we have)
    top_results = results[:2] if len(results) >= 2 else results[:1]

    # Create tasks to fetch articles in parallel
    tasks = []
    for result in top_results:
        url = f"https://radiopaedia.org{result['href']}"
        tasks.append(asyncio.create_task(aget_article_text(url, c)))

    # Wait for all article fetches to complete concurrently
    articles = await asyncio.gather(*tasks)

    # Create Source objects for each result
    sources = [
        Source(title=result["title"], url=f"https://radiopaedia.org{result['href']}")
        for result in top_results
    ]

    # Return both the article texts and the source objects
    return [article + "\n\n" for article in articles], sources


async def aanswer_query(
    query: str, convo: ConversationManager, c: apsw.Cursor, search: bool = True
):
    """Main coroutine to search and answer questions."""
    client = AsyncOpenAI(
        base_url="https://api.together.xyz/v1",
        api_key=os.getenv("TOGETHER_API_KEY"),
    )
    model = "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"

    if not search:
        convo.add_user_message(query)
        result = ""
        async for text in aask_llm(client, model, convo):
            result += text
            yield AnswerChunkEvent(chunk=result)
            await asyncio.sleep(0.025)
        convo.add_assistant_message(result)
        yield StopEvent()
        return

    terms = await aget_search_terms(query)

    # Inform the client that we are starting to search for each term.
    yield SearchEvent(terms=terms)
    await asyncio.sleep(0.025)

    # Create and launch all tasks concurrently for each term.
    tasks = [asyncio.create_task(aprocess_term(term, c)) for term in terms]
    # Wait for all tasks to finish concurrently.
    results = await asyncio.gather(*tasks, return_exceptions=True)

    articles = ""
    sources = []
    # Process the results in the order of the search terms.
    for term, result in zip(terms, results):
        # Handle errors or missing results.
        if isinstance(result, Exception) or result is None:
            yield ErrorEvent(term=term, error=str(result))
            return

        article_texts, term_sources = result
        articles += "".join(article_texts)
        sources.extend(term_sources)
        yield FoundArticleEvent(term=term)
        await asyncio.sleep(0.5)

    prompt = f"<context>{articles}</context>\n\n<query>{query}</query>"

    convo.add_user_message(prompt)

    result = ""
    async for text in aask_llm(client, model, convo):
        result += text if isinstance(text, str) else ""
        yield AnswerChunkEvent(chunk=result)
        await asyncio.sleep(0.025)
    convo.add_assistant_message(result)
    if sources:
        yield SourcesEvent(sources=sources, answer=result)
    yield StopEvent()


async def aask_llm(client, model, convo: ConversationManager):
    response = await client.chat.completions.create(
        model=model, messages=convo.get_messages(), temperature=0.2, stream=True
    )
    async for chunk in response:
        if chunk.choices:
            yield chunk.choices[0].delta.content


async def aanswer_query_csv(query: str, cursor):
    convo = ConversationManager()

    result = {}
    result["query"] = query

    async for event in aanswer_query(query, convo, cursor):
        if isinstance(event, SearchEvent):
            result["search_terms"] = event.terms
        elif isinstance(event, AnswerChunkEvent):
            result["answer"] = event.chunk
        elif isinstance(event, SourcesEvent):
            answer = event.answer
            sources = event.sources
            result["answer"] = answer
            result["urls"] = [source.url for source in sources]
        elif isinstance(event, StopEvent):
            break
        else:
            pass

    return result


# Synchronous versions of async functions

def get_search_terms(query: str) -> list[str]:
    client = OpenAI(
        base_url="https://api.together.xyz/v1",
        api_key=os.getenv("TOGETHER_API_KEY"),
    )
    model = "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"

    message = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": '<examples>\n<example>\n<query>\nWhat are the findings of acute pancreatitis on contrast-enhanced CT?\n</query>\n<ideal_output>\n<analysis>\n1. Main radiological concept: acute pancreatitis\n2. The query does not require a comparison or multiple distinct concepts.\n3. The most appropriate technical term is "acute pancreatitis".\n4. This search term is justified because it directly addresses the main concept in the query. Although the query asks about the cause, searching for "acute pancreatitis" will likely provide information about its etiology, including the most common cause.\n</analysis>\n<search_terms>acute pancreatitis</search_terms>\n</ideal_output>\n</example>\n<example>\n<query>\nWhat is the MTA score?\n</query>\n<ideal_output>\n<analysis>\n1. Main radiological concept: MTA score\n2. The query does not require a comparison or multiple distinct concepts.\n3. The most appropriate technical term is "MTA score".\n4. This search term is justified because it directly addresses the main concept in the query. While the query asks about a specific age and pathological score, searching for "MTA score" will likely provide comprehensive information about the scoring system, including age-related norms and pathological thresholds.\n</analysis>\n<search_terms>MTA score</search_terms>\n</ideal_output>\n</example>\n<example>\n<query>\nHow to differentiate radiation necrosis from tumor recurrence on MRI?\n</query>\n<ideal_output>\n<analysis>\n1. Main radiological concepts: radiation necrosis, tumor recurrence\n2. The query implies a comparison between two conditions, but does not explicitly ask for both to be searched.\n3. The most appropriate technical term is "radiation necrosis".\n4. This search term is justified because it focuses on one of the main concepts in the query. While the question involves differentiating between radiation necrosis and tumor recurrence, searching for "radiation necrosis" will likely provide information on its characteristics and how to distinguish it from tumor recurrence. As per the guidelines, we provide only one search term unless explicitly asked for multiple terms.\n</analysis>\n<search_terms>radiation necrosis</search_terms>\n</ideal_output>\n</example>\n<example>\n<query>\nHow to differentiate primary CNS lymphoma from glioblastoma on MRI?\n</query>\n<ideal_output>\n<analysis>\n1. Main radiological concepts: primary CNS lymphoma, glioblastoma\n2. The query explicitly asks for a comparison between two conditions.\n3. The most appropriate technical terms are "CNS lymphoma" and "glioblastoma".\n4. These search terms are justified because the query specifically asks for a comparison between these two conditions. As per the guidelines, we provide multiple search terms when the query explicitly requires a comparison.\n</analysis>\n<search_terms>CNS lymphoma\nglioblastoma</search_terms>\n</ideal_output>\n</example>\n<example>\n<query>\nHow does a TOF MRA work?\n</query>\n<ideal_output>\n<analysis>\n1. Main radiological concept: TOF MRA (Time-of-Flight Magnetic Resonance Angiography)\n2. The query does not require a comparison or multiple distinct concepts.\n3. The most appropriate technical term is "TOF MRA".\n4. This search term is justified because it directly addresses the main concept in the query. While the question asks about the working principle, searching for "TOF MRA" will likely provide comprehensive information about the technique, including how it works.\n</analysis>\n<search_terms>TOF MRA</search_terms>\n</ideal_output>\n</example>\n<example>\n<query>\nWhat\'s chemical shift imaging?\n</query>\n<ideal_output>\n<analysis>\n1. Main radiological concept: chemical shift imaging\n2. The query does not require a comparison or multiple distinct concepts.\n3. The most appropriate technical term is "chemical shift imaging".\n4. This search term is justified because it directly matches the concept asked about in the query. It is a concise noun phrase that captures the specific imaging technique in question.\n</analysis>\n<search_terms>chemical shift imaging</search_terms>\n</ideal_output>\n</example>\n</examples>\n\n',
                    },
                    {
                        "type": "text",
                        "text": f"<query>{query}</query>",
                    },
                ],
            },
            {"role": "assistant", "content": [{"type": "text", "text": "<analysis>"}]},
        ],
        temperature=0.2,
    )

    search_terms = extract_all_query_content(message.choices[0].message.content)

    logging.info(f"Searchterms for query: '{query}' are: '{search_terms}'")
    return search_terms


def search_results(search_term: str, cursor):
    soup = search_radiopaedia(search_term, cursor)

    all_search_results = [
        structure_search_result(search_result, i)
        for i, search_result in enumerate(soup.find_all(class_="search-result"))
    ]

    return all_search_results


def get_article_text(url, cursor):
    cache_hits = cursor.execute(
        "SELECT content FROM radiopaedia_articles WHERE url = ?", (url,)
    ).fetchall()
    if cache_hits:
        logging.info(f"Cache hit for url: '{url}'")
        return cache_hits[0][0]
    with httpx.Client() as client:
        response = client.get(url, headers=http_headers)
    soup = BeautifulSoup(response.content, "html.parser")
    content = soup.select("#content > div.body.user-generated-content")[0].text.strip()
    cursor.execute(
        "INSERT INTO radiopaedia_articles (url, content) VALUES (?, ?)", (url, content)
    )
    return content


def search_radiopaedia(search_query: str, cursor):
    url = "https://radiopaedia.org/search"
    cache_hits = cursor.execute(
        "SELECT search_results FROM radiopaedia_search_results WHERE search_query = ?",
        (search_query,),
    ).fetchall()
    if cache_hits:
        logging.info(f"Cache hit for search query: '{search_query}'")
        rbody = cache_hits[0][0]
        return BeautifulSoup(rbody, "html.parser")

    params = {"lang": "us", "q": search_query, "scope": "articles"}

    with httpx.Client() as client:
        response = client.get(url, params=params, headers=http_headers)

    soup = BeautifulSoup(response.content, "html.parser")

    if soup.find(class_="search-result"):
        cursor.execute(
            "INSERT INTO radiopaedia_search_results (search_query, search_results) VALUES (?, ?)",
            (search_query, response.content),
        )

    return BeautifulSoup(response.content, "html.parser")


def process_term(term: str, c) -> tuple[list[str], list[Source]]:
    results = search_results(term, c)
    if not results or len(results) == 0:
        return [], []

    top_results = results[:2] if len(results) >= 2 else results[:1]

    articles = []
    for result in top_results:
        url = f"https://radiopaedia.org{result['href']}"
        article = get_article_text(url, c)
        articles.append(article + "\n\n")

    sources = [
        Source(title=result["title"], url=f"https://radiopaedia.org{result['href']}")
        for result in top_results
    ]

    return articles, sources


def answer_query(
    query: str, convo: ConversationManager, c: apsw.Cursor, search: bool = True
):
    client = OpenAI(
        base_url="https://api.together.xyz/v1",
        api_key=os.getenv("TOGETHER_API_KEY"),
    )
    model = "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"

    if not search:
        convo.add_user_message(query)
        result = ""
        for text in ask_llm(client, model, convo):
            result += text
        convo.add_assistant_message(result)
        return result

    terms = get_search_terms(query)

    articles = ""
    sources = []
    for term in terms:
        try:
            article_texts, term_sources = process_term(term, c)
            articles += "".join(article_texts)
            sources.extend(term_sources)
        except Exception as e:
            logging.error(f"Error processing term '{term}': {e}")
            continue

    prompt = f"<context>{articles}</context>\n\n<query>{query}</query>"

    convo.add_user_message(prompt)

    result = ""
    for text in ask_llm(client, model, convo):
        result += text if isinstance(text, str) else ""
    convo.add_assistant_message(result)
    return result, sources


def ask_llm(client, model, convo: ConversationManager):
    response = client.chat.completions.create(
        model=model, messages=convo.get_messages(), temperature=0.2, stream=True
    )
    for chunk in response:
        if chunk.choices:
            yield chunk.choices[0].delta.content


def answer_query_csv(query: str, cursor):
    convo = ConversationManager()
    
    result = {}
    result["query"] = query
    
    try:
        terms = get_search_terms(query)
        result["search_terms"] = terms
        
        answer_result, sources = answer_query(query, convo, cursor)
        result["answer"] = answer_result
        result["urls"] = [source.url for source in sources]
    except Exception as e:
        logging.error(f"Error in answer_query_csv: {e}")
        result["answer"] = "Error processing query"
        result["urls"] = []
    
    return result
