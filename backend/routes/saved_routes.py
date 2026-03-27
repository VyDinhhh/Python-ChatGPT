from flask import Blueprint, jsonify, request
import sqlite3
from models.db import DB_NAME

saved_bp = Blueprint("saved", __name__)

@saved_bp.route("/", methods=["GET"])
def get_saved():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, item_type, title, source, url FROM saved_items")
    rows = cursor.fetchall()
    conn.close()

    items = [
        {
            "id": row[0],
            "item_type": row[1],
            "title": row[2],
            "source": row[3],
            "url": row[4]
        }
        for row in rows
    ]
    return jsonify(items)

@saved_bp.route("/", methods=["POST"])
def save_item():
    data = request.json

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO saved_items (item_type, title, source, url) VALUES (?, ?, ?, ?)",
        (data["item_type"], data["title"], data.get("source"), data["url"])
    )
    conn.commit()
    conn.close()

    return jsonify({"message": "Saved successfully"})

@saved_bp.route("/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM saved_items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()

    return jsonify({"message": "Deleted successfully"})