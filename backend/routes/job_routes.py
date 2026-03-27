from flask import Blueprint, jsonify
from services.jobs_service import fetch_tech_jobs

jobs_bp = Blueprint("jobs", __name__)

@jobs_bp.route("/", methods=["GET"])
def get_jobs():
    try:
        jobs = fetch_tech_jobs()
        return jsonify(jobs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500