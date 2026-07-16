import sqlite3

from flask import Blueprint, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from ..auth_utils import generate_token
from ..db import get_db

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400
    if len(password) < 6:
        return jsonify({"error": "password must be at least 6 characters"}), 400

    db = get_db()
    try:
        cursor = db.execute(
            "INSERT INTO user (email, password_hash) VALUES (?, ?)",
            (email, generate_password_hash(password)),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "An account with this email already exists"}), 409

    token = generate_token(cursor.lastrowid)
    return jsonify({"message": "User registered successfully", "token": token}), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    db = get_db()
    user = db.execute("SELECT * FROM user WHERE email = ?", (email,)).fetchone()

    if user is None or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid email or password"}), 401

    token = generate_token(user["id"])
    return jsonify({"message": "Login successful", "token": token}), 200
