from lib import (
    structure_search_result,
    ErrorEvent,
    StopEvent,
    aanswer_query,
    setup_db
)

from bs4 import BeautifulSoup
import pytest
import dspy
import httpx

@pytest.fixture
def clean_db(monkeypatch):
    fresh_cursor = setup_db(":memory:")
    monkeypatch.setattr("lib.c", fresh_cursor)
    return fresh_cursor

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

@pytest.mark.asyncio
async def test_stream_error_handling(monkeypatch, clean_db):
    # arrange
    def mock_streamify(*args, **kwargs):
        # return a mock that raises when iterated
        async def failing_stream(*args, **kwargs):
            raise Exception("Test error")
        return failing_stream

    monkeypatch.setattr("lib.dspy.streamify", mock_streamify)

    # act
    res = []
    async for e in aanswer_query(query="foobar", history = dspy.History(messages=[])):
        res.append(e)

    # assert
    assert len(res) == 2
    assert isinstance(res[0], ErrorEvent)
    assert isinstance(res[1], StopEvent)

@pytest.mark.asyncio
async def test_http_error(monkeypatch, clean_db):
    # arrange
    def mock_get(*args, **kwargs):
        # return a mock that raises when iterated
        raise httpx.HTTPError("Test error")
    monkeypatch.setattr("lib.client.get", mock_get)

    # act
    res = []
    async for e in aanswer_query(query="What is a meningeoma?", history = dspy.History(messages=[])):
        res.append(e)

    # assert
    print(res)
    assert len(res) == 2
    assert isinstance(res[0], ErrorEvent)
    assert isinstance(res[1], StopEvent)
