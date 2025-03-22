from lib import extract_all_query_content, get_search_terms
from types import SimpleNamespace
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
