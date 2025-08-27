from dotenv import load_dotenv
import logging
import httpx
from bs4 import BeautifulSoup
import apsw
import apsw.bestpractice
import dspy
import os

from dataclasses import dataclass

load_dotenv()

@dataclass
class Source:
    title: str
    url: str


@dataclass
class AnswerChunkEvent:
    answer: str

@dataclass
class FinalAnswerEvent:
    answer: str
    articles: list[dict]

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
    message: str

@dataclass
class StopEvent:
    pass


LogicEvent = (
    AnswerChunkEvent
    | FinalAnswerEvent
    | SearchEvent
    | FoundArticleEvent
    | ErrorEvent
    | SourcesEvent
    | StopEvent
)

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

MODEL = os.getenv("MODEL_NAME", "groq/moonshotai/kimi-k2-instruct")
lm = dspy.LM(MODEL, api_key=os.getenv("GROQ_API_KEY"))
dspy.configure(lm=lm)
c = setup_db(os.getenv("DB_PATH", "data/cache.db"))

class SearchQuerySig(dspy.Signature):
    """Extract one or two main topics (diseases, procedures, phenomenon etc.) from the user query.

    Do not include imaging modalities (CT, MRI etc.) in your topics."""

    user_query: str = dspy.InputField()
    main_topics: list[str] = dspy.OutputField()

class AnswerQuerySig(dspy.Signature):
    """Answer the user query based on the context.

    If the context is not relevant to the user query, say that you don't know. Do not hallucinate answers."""

    user_query: str = dspy.InputField()
    context: list[str] = dspy.InputField()
    history: dspy.History = dspy.InputField()
    answer: str = dspy.OutputField(desc="concise, yet educational, markdown-styled answer to the user query.")


class RadiopaediaArticleFinder(dspy.Module):
    def __init__(self):
        self.generate_search_query = dspy.ChainOfThought(SearchQuerySig)

    def forward(self, user_query: str):
        topics = self.generate_search_query(user_query=user_query).main_topics

        urls = []
        for topic in topics:
            results = search_results(search_term=topic, cursor=c)
            urls.extend(f"https://radiopaedia.org{r['href']}" for r in results[:2])

        return dspy.Prediction(urls=urls, main_topics=topics)

class RadiopaediaQA(dspy.Module):
    def __init__(self, article_finder):
        self.find_articles = article_finder
        self.answer_query = dspy.Predict(AnswerQuerySig)

    def forward(self, user_query: str, history: dspy.History):
        articles = history.messages[0]["articles"] if history.messages else dict(self.find_articles(user_query=user_query))
        if not articles["urls"]:
            return dspy.Prediction(error="No results found")

        context = [get_article_text(url=url, cursor=c) for url in articles["urls"]]
        answer = self.answer_query(user_query=user_query, context=context, history=history).answer
        return dspy.Prediction(answer=answer, context=context, articles=articles)

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

_http_client = None

def get_http_client():
    global _http_client
    if _http_client is None:
        _http_client = httpx.Client(timeout=30.0)
    return _http_client

# module level httpx client
client = get_http_client()

def structure_search_result(result, idx):
    return {
        "id": idx,
        "title": result.find(class_="search-result-title").text.strip(),
        "body": result.find(class_="search-result-body").text.strip(),
        "href": result["href"],
    }

async def aanswer_query(
    query: str, history: dspy.History
):
    """Main coroutine to search and answer questions."""

    find_articles = RadiopaediaArticleFinder()
    find_articles.load(path=os.getenv("OPT_MODEL_PATH")) if os.getenv("OPT_MODEL_PATH") else None
    qa = RadiopaediaQA(find_articles)


    def check_faithfulness(_, pred):
        checker = dspy.ChainOfThought("context, answer -> is_faithful: bool")
        if not pred.context:
            return 0.0
        is_faithful = checker(context=pred.context, answer=pred.answer).is_faithful
        return 1.0 if is_faithful else 0.0

    faithful_qa = dspy.Refine(module=qa, N=3, reward_fn=check_faithfulness, threshold=1.0)

    stream_qa = dspy.streamify(
        faithful_qa,
        stream_listeners=[
            dspy.streaming.StreamListener(signature_field_name="answer")
        ]
    )

    outp_stream = stream_qa(user_query=query, history=history)
    answer = ""
    try:
        async for chunk in outp_stream:
            if isinstance(chunk, dspy.streaming.StreamResponse):
                answer += chunk.chunk
                yield AnswerChunkEvent(answer=answer)
            elif isinstance(chunk, dspy.Prediction):
                yield FinalAnswerEvent(answer=chunk.answer, articles=chunk.articles)
                yield SourcesEvent(sources=[Source(title=url, url=url) for url in list(set(chunk.articles["urls"]))], answer=chunk.answer)
        yield StopEvent()
    except Exception as e:
        logging.error(f"Error occurred: {e}")
        yield ErrorEvent(message="Something went wrong. Please try again.")
        yield StopEvent()

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
    response = client.get(url, headers=http_headers)
    soup = BeautifulSoup(response.text, "html.parser")
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

    response = client.get(url, params=params, headers=http_headers)

    soup = BeautifulSoup(response.text, "html.parser")

    if soup.find(class_="search-result"):
        cursor.execute(
            "INSERT INTO radiopaedia_search_results (search_query, search_results) VALUES (?, ?)",
            (search_query, response.content),
        )

    return BeautifulSoup(response.text, "html.parser")
