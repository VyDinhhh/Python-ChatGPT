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


def is_article_displayable(item: dict) -> bool:
    """
    Basic validation for raw NewsAPI article data before parsing.
    Applies to every article.
    """
    try:
        if not isinstance(item, dict):
            return False

        url = (item.get("url") or "").strip()
        title = (item.get("title") or "").strip()
        description = (item.get("description") or "").strip()
        image_url = (item.get("urlToImage") or "").strip()
        published_at = (item.get("publishedAt") or "").strip()

        # Require a URL
        if not url:
            return False

        # If there is no title, allow description to be used as fallback
        if not title and not description:
            return False

        # Require a publish date for cleaner card display
        if not published_at:
            return False

        # Optional stricter filter:
        # require either image or description so the card looks complete
        if not image_url and not description:
            return False

        return True
    except Exception:
        return False


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
    seen_urls = set()
    total_results = 0

    if not api_key:
        return [], "Missing NEWS_API_KEY. Add it to your .env file.", 0

    # We fetch more raw articles than we display so filtering still leaves
    # enough valid cards on the page.
    raw_batch_size = 8

    # Start from the requested page, then keep going forward until we collect enough.
    current_api_page = page

    # Safety stop so we do not keep requesting forever.
    max_extra_pages = 5
    pages_checked = 0

    while len(articles_to_show) < page_size and pages_checked < max_extra_pages:
        params = {
            "apiKey": api_key,
            "page": current_api_page,
            "pageSize": raw_batch_size,
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

        # No more articles available from API
        if not raw_articles:
            break

        for item in raw_articles:
            try:
                if len(articles_to_show) >= page_size:
                    break

                if not is_article_displayable(item):
                    continue

                url = (item.get("url") or "").strip()
                if url in seen_urls:
                    continue

                title = (item.get("title") or "").strip()
                description = (item.get("description") or "").strip()
                published_at = (item.get("publishedAt") or "").strip()
                image_url = (item.get("urlToImage") or "").strip()

                if not title:
                    title = safe_truncate(description, 80)

                if not url or not title:
                    continue

                parsed = parse_full_article(url)
                if not parsed.get("success"):
                    continue

                full_text = (parsed.get("text") or "").strip()
                if len(full_text) < 200:
                    continue

                short_description = safe_truncate(description or full_text, 180)
                if not short_description:
                    continue

                final_image = parsed.get("top_image") or image_url
                if not final_image:
                    continue

                article_card = {
                    "title": title,
                    "description": short_description,
                    "published_at": published_at,
                    "url": url,
                    "image_url": final_image
                }

                articles_to_show.append(article_card)
                seen_urls.add(url)

            except Exception:
                continue

        current_api_page += 1
        pages_checked += 1

        # Stop if the next API page would clearly be beyond available results
        try:
            if total_results and ((current_api_page - 1) * raw_batch_size) >= total_results:
                break
        except Exception:
            pass

    if not articles_to_show:
        return [], "No readable articles were available for this topic/page. Try another topic.", total_results

    return articles_to_show, "", total_results