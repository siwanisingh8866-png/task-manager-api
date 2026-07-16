from flask import Blueprint, jsonify, request

from ..auth_utils import token_required
from ..db import get_db

tasks_bp = Blueprint("tasks", __name__)

VALID_STATUSES = {"pending", "in_progress", "completed"}


def _serialize(task):
    return {
        "id": task["id"],
        "title": task["title"],
        "description": task["description"],
        "status": task["status"],
        "created_at": task["created_at"],
        "updated_at": task["updated_at"],
    }


@tasks_bp.route("", methods=["GET", "POST"])
@token_required
def tasks_collection(current_user_id):
    db = get_db()

    if request.method == "GET":
        status = request.args.get("status")
        if status:
            rows = db.execute(
                "SELECT * FROM task WHERE user_id = ? AND status = ? ORDER BY created_at DESC",
                (current_user_id, status),
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT * FROM task WHERE user_id = ? ORDER BY created_at DESC",
                (current_user_id,),
            ).fetchall()
        return jsonify([_serialize(r) for r in rows]), 200

    # POST - create a task
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    description = data.get("description", "")
    status = data.get("status", "pending")

    if not title:
        return jsonify({"error": "title is required"}), 400
    if status not in VALID_STATUSES:
        return jsonify({"error": f"status must be one of {sorted(VALID_STATUSES)}"}), 400

    cursor = db.execute(
        "INSERT INTO task (user_id, title, description, status) VALUES (?, ?, ?, ?)",
        (current_user_id, title, description, status),
    )
    db.commit()
    row = db.execute("SELECT * FROM task WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return jsonify(_serialize(row)), 201


@tasks_bp.route("/<int:task_id>", methods=["GET", "PUT", "DELETE"])
@token_required
def task_detail(current_user_id, task_id):
    db = get_db()
    row = db.execute(
        "SELECT * FROM task WHERE id = ? AND user_id = ?", (task_id, current_user_id)
    ).fetchone()

    if row is None:
        return jsonify({"error": "Task not found"}), 404

    if request.method == "GET":
        return jsonify(_serialize(row)), 200

    if request.method == "DELETE":
        db.execute("DELETE FROM task WHERE id = ?", (task_id,))
        db.commit()
        return jsonify({"message": "Task deleted"}), 200

    # PUT - update task
    data = request.get_json(silent=True) or {}
    title = data.get("title", row["title"])
    description = data.get("description", row["description"])
    status = data.get("status", row["status"])

    if status not in VALID_STATUSES:
        return jsonify({"error": f"status must be one of {sorted(VALID_STATUSES)}"}), 400

    db.execute(
        """UPDATE task
           SET title = ?, description = ?, status = ?, updated_at = CURRENT_TIMESTAMP
           WHERE id = ?""",
        (title, description, status, task_id),
    )
    db.commit()
    updated = db.execute("SELECT * FROM task WHERE id = ?", (task_id,)).fetchone()
    return jsonify(_serialize(updated)), 200
