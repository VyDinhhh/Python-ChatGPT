from typing import List, Tuple
import requests
from services.article_parser import parse_full_article

NEWS_API_URL = "https://newsapi.org/v2/top-headlines"


def safe_truncate(text: str, length: int = 180) -> str:
    try:
        cleaned = (text or "").strip()
        if len(cleaned) <= length:
            return cleaned
        return cleaned[:length].rstrip() + "..."
    except Exception:
        return ""


def fetch_articles(
    api_key: str,
    query: str = "",
    topic: str = "technology",
    page: int = 1,
    page_size: int = 4,
    language: str = "en",
    country: str = "us"
) -> Tuple[List[dict], str, int]:
    articles_to_show = []
    total_results = 0

    if not api_key:
        return [], "Missing NEWS_API_KEY. Add it to your .env file.", 0

    params = {
        "apiKey": api_key,
        "page": page,
        "pageSize": page_size,
        "category": topic,
        "country": country
    }

    if query:
        params["q"] = query

    try:
        response = requests.get(NEWS_API_URL, params=params, timeout=15)
        response.raise_for_status()
        payload = response.json()
    except requests.exceptions.RequestException as exc:
        return [], f"Network error while contacting NewsAPI: {exc}", 0
    except ValueError as exc:
        return [], f"Invalid JSON returned from NewsAPI: {exc}", 0
    except Exception as exc:
        return [], f"Unexpected error while contacting NewsAPI: {exc}", 0

    try:
        status = payload.get("status")
        if status != "ok":
            return [], payload.get("message", "NewsAPI returned an error."), 0

        raw_articles = payload.get("articles", [])
        total_results = int(payload.get("totalResults", 0))
    except Exception as exc:
        return [], f"Could not read article list from NewsAPI response: {exc}", 0

    for item in raw_articles:
        try:
            url = (item.get("url") or "").strip()
            title = (item.get("title") or "Untitled").strip()
            description = (item.get("description") or "").strip()
            published_at = (item.get("publishedAt") or "").strip()
            image_url = (item.get("urlToImage") or "").strip()

            if not url or not title:
                continue

            parsed = parse_full_article(url)
            if not parsed.get("success"):
                continue

            full_text = (parsed.get("text") or "").strip()
            if len(full_text) < 200:
                continue

            short_description = safe_truncate(description or full_text, 180)

            article_card = {
                "title": title,
                "description": short_description,
                "published_at": published_at,
                "url": url,
                "image_url": parsed.get("top_image") or image_url
            }
            articles_to_show.append(article_card)

        except Exception:
            continue

    if not articles_to_show:
        return [], "No readable articles were available for this topic/page. Try another topic.", total_results

    return articles_to_show, "", total_results