from flask import Blueprint, jsonify
from services.news_service import fetch_tech_news

news_bp = Blueprint("news", __name__)

@news_bp.route("/", methods=["GET"])
def get_news():
    try:
        articles = fetch_tech_news()
        return jsonify(articles)
    except Exception as e:
        return jsonify({"error": str(e)}), 500