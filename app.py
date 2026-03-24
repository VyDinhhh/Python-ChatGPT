from flask import Flask, render_template, request
from config import Config
from services.news_service import fetch_articles

SUPPORTED_TOPICS = [
    "business",
    "entertainment",
    "general",
    "health",
    "science",
    "sports",
    "technology"
]


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates")
    app.config.from_object(Config)

    @app.route("/", methods=["GET"])
    def home():
        query = (request.args.get("q", default="", type=str) or "").strip()
        topic = (request.args.get("topic", default="technology", type=str) or "technology").strip().lower()
        page = request.args.get("page", default=1, type=int)
        page_size = 4

        if topic not in SUPPORTED_TOPICS:
            topic = "technology"

        try:
            page = max(1, page)
        except Exception:
            page = 1

        try:
            articles, error_message, total_results = fetch_articles(
                api_key=app.config.get("NEWS_API_KEY", ""),
                query=query,
                topic=topic,
                page=page,
                page_size=page_size,
                language="en",
                country="us"
            )
        except Exception as exc:
            articles = []
            error_message = f"Unexpected error while loading news: {exc}"
            total_results = 0

        has_prev = page > 1
        has_next = page * page_size < total_results
        prev_page = page - 1
        next_page = page + 1

        return render_template(
            "home.html",
            articles=articles,
            query=query,
            topic=topic,
            supported_topics=SUPPORTED_TOPICS,
            page=page,
            page_size=page_size,
            total_results=total_results,
            has_prev=has_prev,
            has_next=has_next,
            prev_page=prev_page,
            next_page=next_page,
            error_message=error_message
        )

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("error.html", message="Page not found."), 404

    @app.errorhandler(500)
    def server_error(_error):
        return render_template("error.html", message="Something went wrong on the server."), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)