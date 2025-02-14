import instructor
from anthropic import Anthropic
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import logging
import requests
from bs4 import BeautifulSoup
import apsw
from claudette import models, Chat

load_dotenv()

anthropic = Anthropic()

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


class SearchTerm(BaseModel):
    text: str = Field(
        ...,
        title="The search term extracted from the provided text. The search term should be the underlying disease or condition that the user is asking about.",
    )


class BestSearchResult(BaseModel):
    chain_of_thought: str = Field(
        ..., title="The reason why this is the best search result for the given query."
    )
    id: int = Field(
        ..., title="The id of the best matching search result for the given query."
    )


def get_search_term(query: str) -> SearchTerm:
    # note that client.chat.completions.create will also work
    resp = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=1024,
        messages=[
            {
                "role": "system",
                "content": """You are an very experienced radiologist.
                
                Given the user query, generate a search term that will return a relevant article from Radiopaedia. The search term should be the underlying disease, condition or concept that the user is asking about.
                
                Examples:
                <user_query>What is the most common cause of acute pancreatitis?</user_query>
                <search_term>acute pancreatitis</search_term>
                
                <user_query>What MTA score is pathological for a 77 year old?"</user_query>
                <search_term>MTA score</search_term>
                
                <user_query>How to differentiate radiation necrosis from tumor recurrence?</user_query>
                <search_term>radiation necrosis</search_term>
                
                <user_query>How do I measure the tibial tuberosity-trochlear groove distance?</user_query>
                <search_term>tibial tuberosity-trochlear groove distance</search_term>
                
                <user_query>How does a TOF MRA work?</user_query>
                <search_term>TOF MRA</search_term>
                
                <user_query>What is chemical shift imaging?</user_query>
                <search_term>chemical shift imaging</search_term>""",
            },
            {
                "role": "user",
                "content": f"<user_query>{query}</user_query>",
            },
        ],
        response_model=SearchTerm,
    )

    logging.info(f"SearchTerm for query: '{query}' is: '{resp.text}'")

    return resp


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
    soup = search_radiopaedia(search_term.text, cursor)

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
