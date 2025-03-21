import instructor
from anthropic import Anthropic
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import logging
import requests
from bs4 import BeautifulSoup
import apsw
from claudette import models, Chat

import os
import anthropic
import re

load_dotenv()


ANTHROPIC_MODEL = "claude-3-5-haiku-latest"

client = instructor.from_anthropic(Anthropic())


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


class BestSearchResult(BaseModel):
    chain_of_thought: str = Field(
        ..., title="The reason why this is the best search result for the given query."
    )
    id: int = Field(
        ..., title="The id of the best matching search result for the given query."
    )


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


def get_search_terms(query: str) -> list[str]:
    client = anthropic.Anthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
    )

    message = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=8192,
        temperature=0.6,
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
                        "text": f"You are an experienced radiologist tasked with generating relevant search terms for Radiopaedia based on user queries about radiological topics. Your goal is to identify the core concept(s) or condition(s) mentioned in the query and provide concise, targeted search terms.\n\nHere is the user's query:\n\n<user_query>\n{query}\n</user_query>\n\nPlease analyze the query and determine the most appropriate search term(s). Follow these guidelines:\n\n1. Identify the main radiological concept, condition, or imaging technique mentioned in the query.\n2. If the query explicitly asks for a comparison between two conditions or concepts, provide search terms for both.\n3. In most cases, provide only one search term unless the query specifically demands multiple terms.\n4. Search terms should be concise noun phrases or technical terms, not full questions.\n5. Focus on the underlying medical concept, even if the query is about a specific aspect of that concept.\n\nBefore providing your final output, wrap your analysis in <analysis> tags. In this analysis:\n\n1. List the main radiological concepts or conditions mentioned in the query.\n2. Determine if the query requires a comparison or multiple distinct concepts.\n3. Consider the most appropriate technical term or concise noun phrase for each identified concept.\n4. Justify your choice of search term(s) based on the guidelines provided.\n\nAfter your analysis, provide the search term(s) in the following format:\n\n<search_terms>\n[One search term per line]\n</search_terms>\n\nRemember to only include multiple search terms if the query explicitly requires a comparison or multiple distinct concepts.",
                    },
                ],
            },
            {"role": "assistant", "content": [{"type": "text", "text": "<analysis>"}]},
        ],
    )

    search_terms = extract_all_query_content(message.content[0].text)

    logging.info(f"SearchTerm for query: '{query}' is: '{"', '".join(search_terms)}'")
    return search_terms


def structure_search_result(result, i):
    return {
        "id": i,
        "title": result.find(class_="search-result-title").text.strip(),
        "body": result.find(class_="search-result-body").text.strip(),
        "href": result["href"],
    }


def format_search_results(results):
    def format_single_search_result(result):
        return (
            "ID: "
            + str(result["id"])
            + "\n\n"
            + "Title: "
            + result["title"]
            + "\n\n"
            + "Body: "
            + result["body"]
            + "\n"
        )

    res_string = "\n========================\n\n".join(
        [format_single_search_result(result) for result in results]
    )

    logging.info(f"Formatted search results: \n{res_string}")

    return res_string


def get_best_result(query: str, search_results) -> BestSearchResult:
    # note that client.chat.completions.create will also work
    resp = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=1024,
        temperature=0.0,
        messages=[
            {
                "role": "system",
                "content": """Return the ID of the search result most relevant to the user's query. Base your decision on the title and body of the search results. 

                When in doubt, chose the more general or broad search result. But if there is a specfic search result that is more relevant to the <user_query>, choose that one.
                
                You can only chose one search result. Think about your choice carefully step-by-step.""",
            },
            {
                "role": "user",
                "content": f"query: {query}\n\nsearch_results: {format_search_results(search_results)}",
            },
        ],
        response_model=BestSearchResult,
    )

    logging.info(
        f"BestSearchResult for query: '{query}' is: '{resp.id}' - {resp.chain_of_thought}"
    )

    return resp


def search_results(search_term: str, cursor):
    soup = search_radiopaedia(search_term, cursor)

    all_search_results = [
        structure_search_result(search_result, i)
        for i, search_result in enumerate(soup.find_all(class_="search-result"))
    ][:5]

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


def get_article_text(url, cursor):
    cache_hits = cursor.execute(
        "SELECT content FROM radiopaedia_articles WHERE url = ?", (url,)
    ).fetchall()
    if cache_hits:
        logging.info(f"Cache hit for url: '{url}'")
        return cache_hits[0][0]
    response = requests.get(url, headers=http_headers)
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

    response = requests.get(url, params=params, headers=http_headers)

    cursor.execute(
        "INSERT INTO radiopaedia_search_results (search_query, search_results) VALUES (?, ?)",
        (search_query, response.content),
    )

    return BeautifulSoup(response.content, "html.parser")


def create_chat():
    model = models[-1]  # currently 3.5 haiku

    sp = """Answer the user query faithfully using the information in the context. 
    
    If you don't know the answer don't fabricate an answer, just say 'I don't know'. 
    
    Don't start your answer with something like 'Based on the context...'. Do not mention the context in your answer. This is very important Return the answer directly."""

    return Chat(model, sp=sp, cache=True)
