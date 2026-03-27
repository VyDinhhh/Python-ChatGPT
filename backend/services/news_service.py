import requests
from config import Config

def fetch_item(item_id):
    response = requests.get(f"{Config.HN_BASE_URL}/item/{item_id}.json", timeout=10)
    response.raise_for_status()
    return response.json()

def fetch_tech_news(limit=10):
    response = requests.get(f"{Config.HN_BASE_URL}/topstories.json", timeout=10)
    response.raise_for_status()
    story_ids = response.json()[:limit]

    articles = []
    for item_id in story_ids:
        item = fetch_item(item_id)

        if not item:
            continue

        if item.get("type") != "story":
            continue

        articles.append({
            "title": item.get("title"),
            "source": "Hacker News",
            "author": item.get("by"),
            "description": item.get("text") or f"Score: {item.get('score', 0)} | Comments: {item.get('descendants', 0)}",
            "url": item.get("url") or f"https://news.ycombinator.com/item?id={item.get('id')}",
            "image_url": None,
            "published_at": item.get("time"),
            "type": "news"
        })

    return articles