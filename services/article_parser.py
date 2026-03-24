from newspaper import Article


FORBIDDEN_MARKERS = [
    "403",
    "forbidden",
    "access denied",
    "captcha",
    "please enable javascript",
    "subscribe to continue"
]


def parse_full_article(url: str, timeout: int = 10) -> dict:
    """
    Download and parse a news article with newspaper3k.
    Returns a dictionary with parsed content and status.
    """
    result = {
        "success": False,
        "text": "",
        "top_image": "",
        "authors": [],
        "error": ""
    }

    if not url:
        result["error"] = "Missing article URL."
        return result

    try:
        article = Article(url)
        article.download()
        article.parse()

        parsed_text = (article.text or "").strip()
        lower_text = parsed_text.lower()

        if not parsed_text:
            result["error"] = "Article content is empty after parsing."
            return result

        if any(marker in lower_text for marker in FORBIDDEN_MARKERS):
            result["error"] = "Article appears blocked or forbidden."
            return result

        result["success"] = True
        result["text"] = parsed_text
        result["top_image"] = article.top_image or ""
        result["authors"] = article.authors or []
        return result

    except Exception as exc:
        message = str(exc).lower()
        if "403" in message or "forbidden" in message:
            result["error"] = "Article is forbidden by the publisher."
        else:
            result["error"] = f"Unable to parse article: {exc}"
        return result