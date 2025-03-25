from lib import (
    extract_all_query_content,
    get_search_terms,
    get_docs,
    structure_search_result,
)
from types import SimpleNamespace
from bs4 import BeautifulSoup
import pytest


# Create a fake messages object that returns a fake message.
class FakeMessages:
    async def create(self, **kwargs):
        # Create a fake message where 'content' is a list of objects with a 'text' attribute.
        fake_message = SimpleNamespace()
        fake_message.content = [
            SimpleNamespace(
                text="Some irrelevant text <search_terms>test term</search_terms> more text."
            )
        ]
        return fake_message


# Create a fake Anthropics client.
class FakeClient:
    def __init__(self, *args, **kwargs):
        self.messages = FakeMessages()


# Define a fake constructor for anthropic.Anthropic.
def fake_anthropic_constructor(api_key):
    return FakeClient()


@pytest.mark.asyncio
async def test_get_search_terms(monkeypatch):
    # Arrange

    # Patch the anthropic.Anthropic class in your module to use our fake constructor.
    monkeypatch.setattr("lib.AsyncAnthropic", fake_anthropic_constructor)
    # Set the API key in the environment.
    monkeypatch.setenv("ANTHROPIC_API_KEY", "dummy-api-key")

    # Act
    result = await get_search_terms("Some radiology query")

    # Assert
    assert result == ["test term"]


def test_extract_all_query_content_empty_string():
    assert extract_all_query_content("") == []


def test_extract_all_query_content_no_tags():
    text = "some random text without tags"
    assert extract_all_query_content(text) == []


def test_extract_all_query_content_wrong_tag():
    text = "<wrong_tag>some random text</wrong_tag>"
    assert extract_all_query_content(text) == []


def test_extract_all_query_content_empty_tags():
    text = "<search_terms></search_terms>"
    assert extract_all_query_content(text) == []


def test_extract_all_query_content_single_term():
    text = "<search_terms>acute pancreatitis</search_terms>"
    assert extract_all_query_content(text) == ["acute pancreatitis"]


def test_extract_all_query_content_multiple_terms():
    text = """<search_terms>
    CNS lymphoma
    glioblastoma
    </search_terms>"""
    assert extract_all_query_content(text) == ["CNS lymphoma", "glioblastoma"]


def test_extract_all_query_content_with_whitespace():
    text = """<search_terms>
    
    TOF MRA   
        chemical shift imaging
    
    </search_terms>"""
    assert extract_all_query_content(text) == ["TOF MRA", "chemical shift imaging"]


def test_get_docs():
    # Arrange
    search_results = [
        {
            "title": "Document 1",
            "body": "Summary of Document 1",
        },
        {
            "title": "Document 2",
            "body": "Summary of Document 2",
        },
    ]

    # Act
    results = get_docs(search_results)

    # Assert
    assert results == [
        "Document 1 Summary of Document 1",
        "Document 2 Summary of Document 2",
    ]


def test_single_get_docs():
    # Arrange
    search_results = [
        {
            "title": "Document 1",
            "body": "Summary of Document 1",
        }
    ]

    # Act
    results = get_docs(search_results)

    # Assert
    assert results == ["Document 1 Summary of Document 1"]


def test_structure_search_results():
    # Arrange
    search_result = """<a class="search-result search-result-article" href="/articles/hepatic-adenoma?lang=us">
  <div class="col-xs-12 no-padding">
    <div class="search-result-header">
      <div class="search-result-type label label-article">
        Article
      </div>
      <div class="search-result-title">
        <h4 class="search-result-title-text">
          Hepatic adenoma
        </h4>
      </div>
    </div>
  </div>
  <div class="search-result-body">
    
Hepatic adenomas,&nbsp;or hepatocellular adenomas (HCA), are benign,&nbsp;generally hormone-induced liver tumors. They are usually solitary but can be multiple. Most adenomas have a predilection for hemorrhage, and they must be differentiated from other focal liver lesions due to the risk of HCC transform...
  </div>
</a>"""

    result_soup = BeautifulSoup(search_result, "html.parser")

    # Act
    result = structure_search_result(result_soup.find(class_="search-result"), 0)

    print("result: ", result)
    # Assert
    assert result["id"] == 0
    assert result["title"] == "Hepatic adenoma"
    assert result["href"] == "/articles/hepatic-adenoma?lang=us"
