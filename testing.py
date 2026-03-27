import unittest
from unittest.mock import patch
import requests

from services.news_service import fetch_articles


class MockResponse:
    """
    Simple fake response object used to simulate requests.get(...)
    """
    def __init__(self, payload=None, raise_error=None):
        self.payload = payload or {}
        self.raise_error = raise_error

    def raise_for_status(self):
        if self.raise_error:
            raise self.raise_error

    def json(self):
        return self.payload


class TestFetchArticles(unittest.TestCase):
    # This test verifies that the function immediately returns an error
    # when no News API key is provided.
    def test_missing_api_key_returns_error(self):
        articles, error_message, total_results = fetch_articles(
            api_key="",
            query="ai",
            topic="technology",
            page=1,
            page_size=4
        )

        self.assertEqual(articles, [])
        self.assertIn("Missing NEWS_API_KEY", error_message)
        self.assertEqual(total_results, 0)

    # This test verifies the happy path:
    # - NewsAPI returns one article
    # - parse_full_article succeeds
    # - the article is included in the final result
    @patch("services.news_service.parse_full_article")
    @patch("services.news_service.requests.get")
    def test_successful_fetch_returns_article(self, mock_get, mock_parse):
        fake_payload = {
            "status": "ok",
            "totalResults": 1,
            "articles": [
                {
                    "url": "https://example.com/article-1",
                    "title": "AI Breakthrough",
                    "description": "A useful AI description",
                    "publishedAt": "2026-03-24T10:00:00Z",
                    "urlToImage": "https://example.com/image.jpg"
                }
            ]
        }

        mock_get.return_value = MockResponse(payload=fake_payload)
        mock_parse.return_value = {
            "success": True,
            "text": "A" * 250,
            "top_image": "https://example.com/parsed.jpg",
            "authors": ["Author One"]
        }

        articles, error_message, total_results = fetch_articles(
            api_key="valid-key",
            query="ai",
            topic="technology",
            page=1,
            page_size=4
        )

        self.assertEqual(error_message, "")
        self.assertEqual(total_results, 1)
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0]["title"], "AI Breakthrough")
        self.assertEqual(articles[0]["description"], "A useful AI description")
        self.assertEqual(articles[0]["published_at"], "2026-03-24T10:00:00Z")
        self.assertEqual(articles[0]["url"], "https://example.com/article-1")
        self.assertEqual(articles[0]["image_url"], "https://example.com/parsed.jpg")

    # This test checks that the fallback image from NewsAPI is used
    # when the parser does not return a top image.
    @patch("services.news_service.parse_full_article")
    @patch("services.news_service.requests.get")
    def test_uses_newsapi_image_when_parser_has_no_image(self, mock_get, mock_parse):
        fake_payload = {
            "status": "ok",
            "totalResults": 1,
            "articles": [
                {
                    "url": "https://example.com/article-2",
                    "title": "Space Update",
                    "description": "A space article",
                    "publishedAt": "2026-03-24T11:00:00Z",
                    "urlToImage": "https://example.com/newsapi-image.jpg"
                }
            ]
        }

        mock_get.return_value = MockResponse(payload=fake_payload)
        mock_parse.return_value = {
            "success": True,
            "text": "B" * 250,
            "top_image": "",
            "authors": []
        }

        articles, error_message, total_results = fetch_articles(
            api_key="valid-key",
            query="space",
            topic="science",
            page=1,
            page_size=4
        )

        self.assertEqual(error_message, "")
        self.assertEqual(total_results, 1)
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0]["image_url"], "https://example.com/newsapi-image.jpg")

    # This test verifies that an article is skipped if parse_full_article
    # reports that the article cannot be parsed successfully.
    @patch("services.news_service.parse_full_article")
    @patch("services.news_service.requests.get")
    def test_skips_article_when_parser_fails(self, mock_get, mock_parse):
        fake_payload = {
            "status": "ok",
            "totalResults": 1,
            "articles": [
                {
                    "url": "https://example.com/blocked",
                    "title": "Blocked Article",
                    "description": "Should not be displayed",
                    "publishedAt": "2026-03-24T12:00:00Z",
                    "urlToImage": "https://example.com/image.jpg"
                }
            ]
        }

        mock_get.return_value = MockResponse(payload=fake_payload)
        mock_parse.return_value = {
            "success": False,
            "text": "",
            "top_image": "",
            "authors": [],
            "error": "Forbidden"
        }

        articles, error_message, total_results = fetch_articles(
            api_key="valid-key",
            query="blocked",
            topic="general",
            page=1,
            page_size=4
        )

        self.assertEqual(articles, [])
        self.assertIn("No readable articles", error_message)
        self.assertEqual(total_results, 1)

    # This test verifies that an article is skipped when extracted content
    # is too short to be considered useful for display.
    @patch("services.news_service.parse_full_article")
    @patch("services.news_service.requests.get")
    def test_skips_article_when_extracted_text_is_too_short(self, mock_get, mock_parse):
        fake_payload = {
            "status": "ok",
            "totalResults": 1,
            "articles": [
                {
                    "url": "https://example.com/short",
                    "title": "Short Article",
                    "description": "Short description",
                    "publishedAt": "2026-03-24T13:00:00Z",
                    "urlToImage": "https://example.com/image.jpg"
                }
            ]
        }

        mock_get.return_value = MockResponse(payload=fake_payload)
        mock_parse.return_value = {
            "success": True,
            "text": "Too short",
            "top_image": "https://example.com/parsed.jpg",
            "authors": []
        }

        articles, error_message, total_results = fetch_articles(
            api_key="valid-key",
            query="short",
            topic="general",
            page=1,
            page_size=4
        )

        self.assertEqual(articles, [])
        self.assertIn("No readable articles", error_message)
        self.assertEqual(total_results, 1)

    # This test verifies that an article with no URL is ignored,
    # because the parser cannot fetch content without a URL.
    @patch("services.news_service.parse_full_article")
    @patch("services.news_service.requests.get")
    def test_skips_article_with_missing_url(self, mock_get, mock_parse):
        fake_payload = {
            "status": "ok",
            "totalResults": 1,
            "articles": [
                {
                    "url": "",
                    "title": "No URL Article",
                    "description": "Invalid article",
                    "publishedAt": "2026-03-24T14:00:00Z",
                    "urlToImage": "https://example.com/image.jpg"
                }
            ]
        }

        mock_get.return_value = MockResponse(payload=fake_payload)

        articles, error_message, total_results = fetch_articles(
            api_key="valid-key",
            query="news",
            topic="general",
            page=1,
            page_size=4
        )

        self.assertEqual(articles, [])
        self.assertIn("No readable articles", error_message)
        self.assertEqual(total_results, 1)
        mock_parse.assert_not_called()

    # This test verifies that an article with no title is ignored,
    # because the UI requires a title for display.
    # This test verifies that when title is missing,
# the description is used as a fallback title
# and the article is still included.
    @patch("services.news_service.parse_full_article")
    @patch("services.news_service.requests.get")
    def test_missing_title_uses_description_as_fallback(self, mock_get, mock_parse):
        fake_payload = {
            "status": "ok",
            "totalResults": 1,
            "articles": [
                {
                    "url": "https://example.com/no-title",
                    "title": "",
                    "description": "Fallback title from description",
                    "publishedAt": "2026-03-24T15:00:00Z",
                    "urlToImage": "https://example.com/image.jpg"
                }
            ]
        }

        mock_get.return_value = MockResponse(payload=fake_payload)
        mock_parse.return_value = {
            "success": True,
            "text": "E" * 250,
            "top_image": "",
            "authors": []
        }

        articles, error_message, total_results = fetch_articles(
            api_key="valid-key",
            query="news",
            topic="general",
            page=1,
            page_size=4
        )

        self.assertEqual(error_message, "")
        self.assertEqual(total_results, 1)
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0]["title"], "Fallback title from description")
        self.assertEqual(articles[0]["published_at"], "2026-03-24T15:00:00Z")
        self.assertEqual(articles[0]["url"], "https://example.com/no-title")

    # This test verifies that the function handles a network-level error,
    # such as connection failure or timeout, without crashing.
    @patch("services.news_service.requests.get")
    def test_handles_request_exception(self, mock_get):
        mock_get.side_effect = requests.exceptions.RequestException("Connection failed")

        articles, error_message, total_results = fetch_articles(
            api_key="valid-key",
            query="ai",
            topic="technology",
            page=1,
            page_size=4
        )

        self.assertEqual(articles, [])
        self.assertIn("Network error while contacting NewsAPI", error_message)
        self.assertEqual(total_results, 0)

    # This test verifies that the function handles invalid JSON returned
    # by the API response object.
    @patch("services.news_service.requests.get")
    def test_handles_invalid_json_response(self, mock_get):
        class BadJsonResponse:
            def raise_for_status(self):
                pass

            def json(self):
                raise ValueError("Invalid JSON")

        mock_get.return_value = BadJsonResponse()

        articles, error_message, total_results = fetch_articles(
            api_key="valid-key",
            query="ai",
            topic="technology",
            page=1,
            page_size=4
        )

        self.assertEqual(articles, [])
        self.assertIn("Invalid JSON returned from NewsAPI", error_message)
        self.assertEqual(total_results, 0)

    # This test verifies that NewsAPI error payloads are surfaced properly,
    # such as invalid API key or rate-limiting responses.
    @patch("services.news_service.requests.get")
    def test_handles_newsapi_error_status(self, mock_get):
        fake_payload = {
            "status": "error",
            "message": "API key invalid"
        }

        mock_get.return_value = MockResponse(payload=fake_payload)

        articles, error_message, total_results = fetch_articles(
            api_key="bad-key",
            query="ai",
            topic="technology",
            page=1,
            page_size=4
        )

        self.assertEqual(articles, [])
        self.assertEqual(error_message, "API key invalid")
        self.assertEqual(total_results, 0)

    # This test verifies that multiple raw articles can be filtered so that
    # only the readable and valid ones remain in the final output.
    @patch("services.news_service.parse_full_article")
    @patch("services.news_service.requests.get")
    def test_mixed_articles_only_keeps_valid_ones(self, mock_get, mock_parse):
        fake_payload = {
            "status": "ok",
            "totalResults": 3,
            "articles": [
                {
                    "url": "https://example.com/valid-1",
                    "title": "Valid Article",
                    "description": "A valid description",
                    "publishedAt": "2026-03-24T16:00:00Z",
                    "urlToImage": "https://example.com/image1.jpg"
                },
                {
                    "url": "https://example.com/blocked-2",
                    "title": "Blocked Article",
                    "description": "Should be skipped",
                    "publishedAt": "2026-03-24T16:10:00Z",
                    "urlToImage": "https://example.com/image2.jpg"
                },
                {
                    "url": "",
                    "title": "Missing URL",
                    "description": "Should also be skipped",
                    "publishedAt": "2026-03-24T16:20:00Z",
                    "urlToImage": "https://example.com/image3.jpg"
                }
            ]
        }

        mock_get.return_value = MockResponse(payload=fake_payload)

        def parse_side_effect(url):
            if "valid-1" in url:
                return {
                    "success": True,
                    "text": "C" * 250,
                    "top_image": "https://example.com/parsed-valid.jpg",
                    "authors": []
                }
            return {
                "success": False,
                "text": "",
                "top_image": "",
                "authors": [],
                "error": "Forbidden"
            }

        mock_parse.side_effect = parse_side_effect

        articles, error_message, total_results = fetch_articles(
            api_key="valid-key",
            query="mixed",
            topic="general",
            page=1,
            page_size=4
        )

        self.assertEqual(error_message, "")
        self.assertEqual(total_results, 3)
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0]["title"], "Valid Article")

        # This test verifies that the function sends the expected topic, page,
    # and raw fetch batch size values to NewsAPI.
    @patch("services.news_service.parse_full_article")
    @patch("services.news_service.requests.get")
    def test_sends_expected_request_parameters(self, mock_get, mock_parse):
        fake_payload = {
            "status": "ok",
            "totalResults": 1,
            "articles": [
                {
                    "url": "https://example.com/article-params",
                    "title": "Params Article",
                    "description": "Parameter check",
                    "publishedAt": "2026-03-24T17:00:00Z",
                    "urlToImage": "https://example.com/image.jpg"
                }
            ]
        }

        mock_get.return_value = MockResponse(payload=fake_payload)
        mock_parse.return_value = {
            "success": True,
            "text": "D" * 250,
            "top_image": "",
            "authors": []
        }

        fetch_articles(
            api_key="valid-key",
            query="economy",
            topic="business",
            page=3,
            page_size=4,
            country="us"
        )

        mock_get.assert_called_once()
        called_kwargs = mock_get.call_args.kwargs
        params = called_kwargs["params"]

        self.assertEqual(params["category"], "business")
        self.assertEqual(params["page"], 3)
        self.assertEqual(params["pageSize"], 8)
        self.assertEqual(params["country"], "us")
        self.assertEqual(params["q"], "economy")
        self.assertEqual(params["apiKey"], "valid-key")


if __name__ == "__main__":
    unittest.main()