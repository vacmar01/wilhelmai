import instructor
from anthropic import Anthropic
from pydantic import BaseModel, Field
from dotenv import load_dotenv

import requests
from bs4 import BeautifulSoup

load_dotenv()

anthropic = Anthropic()

ANTHROPIC_MODEL = "claude-3-5-haiku-latest"

anthropic = Anthropic()
client = instructor.from_anthropic(Anthropic())

http_headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'accept-language': 'de-DE,de;q=0.7',
        'cache-control': 'max-age=0',
        'cookie': '*radiopaedia*session=FK2kLR8%2Bhkzg8D5gtP4N4x7y7QoL55kFD40yMiPSOY7%2FN2z7QD85jgYgOl36adv2O4KM%2Buk9%2BIxtFUDX3LTHoSSOeoykDZyd%2FLqq5OPox0tzbn1URW4n5oZhowZCpw9MHPRvZ%2FAIDDhAtaJxz7Ue3hBb%2BjcKRloPcYbUjUBOi4KvtINrFnKpfey%2B13AgAz8bcuzLURQiO07IXbnVRackkRXpgG0mBcjh8n1Ap849t33s81SgYXTXFGeBit4JVhTtqLGrUa%2F%2FIXFZZyKREUk9b8kQYmvUIRtE9Fmr1Rd43JQOa60hTs%2F4Vhh%2F1rClz1pAgZrzAIEDbzx%2Bvz1CKDU%2FhHlydPYIcvrhZXOQ6TKhRDV8bfrfKjjToXAH9vyFbq4VxlnAnyoCA4JBFetkzZbrqrZSYsM%2F%2BF7LW8Swh92pLtO%2BwAps555wlyXnQKDbrapf%2FNaABd3%2Bk301t64uwC1n4nkq3Z7rIG409N%2FFfzylkrNs1eOArX1j%2FqkilucHBXMt--A7TmaE8Ut8M5kXCo--txKn9l3AgN8d8znLnEjAKw%3D%3D',
        'priority': 'u=0, i',
        'sec-ch-ua': '"Chromium";v="128", "Not;A=Brand";v="24", "Brave";v="128"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate', 
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'sec-gpc': '1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
    }

class SearchTerm(BaseModel):
    text: str = Field(..., title="The search term extracted from the provided text. The search term should be the underlying disease or condition that the user is asking about.")
    
class BestSearchResult(BaseModel):
    chain_of_thought: str = Field(..., title="The reason why this is the best search result for the given query.")
    id: int = Field(..., title="The id of the best matching search result for the given query.")

def get_search_term(query: str) -> SearchTerm:
# note that client.chat.completions.create will also work
    resp = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=1024,
        messages=[
            {
                "role": "system",
                "content": "Extract a search term from the provided text.",},
            {
                "role": "user",
                "content": f"text: {query}",
            }
        ],
        response_model=SearchTerm,
    )
    
    print("SearchTerm for query: ", query, "is: ", resp.text)

    return resp

def search_radiopaedia(search_query: str):
    url = 'https://radiopaedia.org/search'


    params = {
        'lang': 'us',
        'q': search_query,
        'scope': 'articles'
    }

    response = requests.get(url, params=params, headers=http_headers)

    soup = BeautifulSoup(response.content, "html.parser")
    return soup

def structure_search_result(result, i): 
    return {
        "id": i,
        "title": result.find(class_='search-result-title').text.strip(),
        "body": result.find(class_='search-result-body').text.strip(),
        "href": result['href']
    }
    
def format_search_results(results):
    def format_single_search_result(result): 
        return "ID: " + str(result['id']) + "\n\n" + "Title: " + result['title'] + "\n\n" + "Body: " + result['body'] + "\n"
    
    res_string = "\n========================\n\n".join([format_single_search_result(result) for result in results])
    
    print(res_string)
    
    return res_string

def get_best_result(query: str, search_results) -> SearchTerm:
# note that client.chat.completions.create will also work
    resp = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=1024,
        messages=[
            {
                "role": "system",
                "content": "return the id of the best matching search result for the given query."},
            {
                "role": "user",
                "content": f"query: {query}\n\nsearch_results: {format_search_results(search_results)}",
            }
        ],
        response_model=BestSearchResult,
    )

    print("BestSearchResult for query: ", query, "is: ", search_results[resp.id])
    
    return resp

def get_article_text(url): 
    response = requests.get(url, headers=http_headers)
    soup = BeautifulSoup(response.content, "html.parser")
    return soup.select("#content > div.body.user-generated-content")[0].text.strip()

def query_for_qa(article_text, query):
    return anthropic.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": f"Answer the user query faithfully using the information in the context. If you don't know the answer don't fabricate an answer, just say 'I don't know'.\n\ncontext: {article_text}\n\nquery: {query}",
                }
            ]
        )
    
def answer_question(query: str) -> str:
    search_term = get_search_term(query)
    soup = search_radiopaedia(search_term.text)
    all_search_results = [structure_search_result(search_result, i) for i, search_result in enumerate(soup.find_all(class_='search-result'))]
    r = get_best_result(query, all_search_results)
    all_search_results[r.id]
    article_text = get_article_text(f"https://radiopaedia.org{all_search_results[r.id]['href']}")

    res = anthropic.messages.create(
            model="claude-3-5-haiku-latest",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": f"Answer the user query faithfully using the information in the context. If you don't know the answer don't fabricate an answer, just say 'I don't know'. Don't start your answer with 'according to the context' or something similar. Just start with the actual answer.\n\ncontext: {article_text}\n\nquery: {query}",
                }
            ]
        )
    
    print(res)
    
    return res.content[0].text, "https://radiopaedia.org" + all_search_results[r.id]['href']
