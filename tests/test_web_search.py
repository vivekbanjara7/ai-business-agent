
import pytest
from unittest.mock import patch, Mock

from tools import web_search


# 1. Successful search
@patch("tools.requests.get")
def test_successful_search(mock_get):
    mock_response = Mock()
    mock_response.json.return_value = {
        "query": "best blogging platforms",
        "total_results": 2,
        "results": [
            {
                "title": "WordPress",
                "url": "https://wordpress.org",
                "site_name": "WordPress",
                "snippet": "A popular blogging platform.",
                "position": 1,
            }
        ],
    }
    mock_get.return_value = mock_response

    with patch.dict("os.environ", {"TINYFISH_API_KEY": "fake_test_key"}):
        result = web_search("best blogging platforms")

    assert result["success"] is True
    assert result["query"] == "best blogging platforms"
    assert result["result_count"] == 1
    assert result["results"][0]["title"] == "WordPress"


# 2. Empty search query
def test_empty_query():
    with pytest.raises(ValueError, match="non-empty string"):
        web_search("")


# 3. Missing API key
def test_missing_api_key():
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(RuntimeError, match="TINYFISH_API_KEY"):
            web_search("test search")


# 4. API timeout
@patch("tools.requests.get")
def test_api_timeout(mock_get):
    import requests

    mock_get.side_effect = requests.exceptions.Timeout()

    with patch.dict("os.environ", {"TINYFISH_API_KEY": "fake_test_key"}):
        with pytest.raises(requests.exceptions.Timeout):
            web_search("test search")


# 5. HTTP server error
@patch("tools.requests.get")
def test_http_error(mock_get):
    import requests

    mock_response = Mock()
    mock_response.raise_for_status.side_effect = (
        requests.exceptions.HTTPError("500 Server Error")
    )
    mock_get.return_value = mock_response

    with patch.dict("os.environ", {"TINYFISH_API_KEY": "fake_test_key"}):
        with pytest.raises(requests.exceptions.HTTPError):
            web_search("test search")


# 6. Invalid JSON response
@patch("tools.requests.get")
def test_invalid_json(mock_get):
    mock_response = Mock()
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_get.return_value = mock_response

    with patch.dict("os.environ", {"TINYFISH_API_KEY": "fake_test_key"}):
        with pytest.raises(ValueError, match="invalid JSON"):
            web_search("test search")


# 7. Unexpected response format
@patch("tools.requests.get")
def test_unexpected_response_format(mock_get):
    mock_response = Mock()
    mock_response.json.return_value = ["unexpected", "data"]
    mock_get.return_value = mock_response

    with patch.dict("os.environ", {"TINYFISH_API_KEY": "fake_test_key"}):
        with pytest.raises(ValueError, match="unexpected response format"):
            web_search("test search")


# 8. Maximum 10 results
@patch("tools.requests.get")
def test_maximum_results(mock_get):
    mock_response = Mock()
    mock_response.json.return_value = {
        "results": [
            {
                "title": f"Result {i}",
                "url": f"https://example.com/{i}",
            }
            for i in range(15)
        ]
    }
    mock_get.return_value = mock_response

    with patch.dict("os.environ", {"TINYFISH_API_KEY": "fake_test_key"}):
        result = web_search("test search")

    assert result["result_count"] == 10
    assert len(result["results"]) == 10


# 9. Long snippet limitation
@patch("tools.requests.get")
def test_long_snippet_limit(mock_get):
    mock_response = Mock()
    mock_response.json.return_value = {
        "results": [
            {
                "title": "Example",
                "snippet": "A" * 2000,
            }
        ]
    }
    mock_get.return_value = mock_response

    with patch.dict("os.environ", {"TINYFISH_API_KEY": "fake_test_key"}):
        result = web_search("test search")

    assert len(result["results"][0]["snippet"]) == 1200


# 10. Invalid result entries are skipped
@patch("tools.requests.get")
def test_invalid_result_entries(mock_get):
    mock_response = Mock()
    mock_response.json.return_value = {
        "results": [
            {"title": "Valid result"},
            "invalid entry",
            None,
            123,
        ]
    }
    mock_get.return_value = mock_response

    with patch.dict("os.environ", {"TINYFISH_API_KEY": "fake_test_key"}):
        result = web_search("test search")

    assert result["result_count"] == 1
    assert result["results"][0]["title"] == "Valid result"
