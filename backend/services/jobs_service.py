import requests
from config import Config

def fetch_item(item_id):
    response = requests.get(f"{Config.HN_BASE_URL}/item/{item_id}.json", timeout=10)
    response.raise_for_status()
    return response.json()

def fetch_tech_jobs(limit=10):
    response = requests.get(f"{Config.HN_BASE_URL}/jobstories.json", timeout=10)
    response.raise_for_status()
    job_ids = response.json()[:limit]

    jobs = []
    for item_id in job_ids:
        item = fetch_item(item_id)

        if not item:
            continue

        if item.get("type") != "job":
            continue

        jobs.append({
            "title": item.get("title"),
            "company": "Hacker News",
            "location": "Not specified",
            "description": item.get("text") or "HN job post",
            "url": item.get("url") or f"https://news.ycombinator.com/item?id={item.get('id')}",
            "salary_min": None,
            "salary_max": None,
            "created": item.get("time"),
            "type": "job"
        })

    return jobs