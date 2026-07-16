import datetime
from functools import wraps

import jwt
from flask import current_app, jsonify, request


def generate_token(user_id: int) -> str:
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now
        + datetime.timedelta(minutes=current_app.config["JWT_EXPIRES_MINUTES"]),
    }
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")


def decode_token(token: str):
    return jwt.decode(
        token, current_app.config["SECRET_KEY"], algorithms=["HS256"]
    )


def token_required(f):
    """Decorator that protects a route behind a Bearer JWT and injects
    the authenticated user's id as `current_user_id`.
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401

        token = auth_header.split(" ", 1)[1]
        try:
            payload = decode_token(token)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        return f(*args, current_user_id=int(payload["sub"]), **kwargs)

    return wrapper
