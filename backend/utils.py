# utils.py
import bcrypt
import jwt
import os
from functools import wraps
from flask import request, jsonify, g
from backend.dbb import get_connection
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET", "supersecret_for_hackathon")
JWT_ALGO = "HS256"
JWT_EXP_DAYS = int(os.getenv("JWT_EXP_DAYS", "7"))

# Password hashing
def hash_password(plain_password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain_password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed.encode('utf-8'))

# JWT
def generate_jwt(payload: dict):
    payload_copy = payload.copy()
    payload_copy["exp"] = datetime.utcnow() + timedelta(days=JWT_EXP_DAYS)
    return jwt.encode(payload_copy, JWT_SECRET, algorithm=JWT_ALGO)

def decode_jwt(token: str):
    try:
        data = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        return data
    except jwt.ExpiredSignatureError:
        return None
    except Exception:
        return None

# Auth decorators
def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", None)
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Authorization header required"}), 401
        token = auth_header.split(" ")[1]
        user = decode_jwt(token)
        if not user:
            return jsonify({"error": "Invalid or expired token"}), 401
        # set g.user for route
        g.user = user
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    @auth_required
    def decorated(*args, **kwargs):
        user = g.user
        if "role" not in user or user["role"] != "ADMIN":
            return jsonify({"error": "Admin privilege required"}), 403
        return f(*args, **kwargs)
    return decorated

# Audit log helper
def write_audit(user_id: int, action_type: str, target_id=None, target_table=None, details=None):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Audit_Logs (user_id, action_type, target_id, target_table, action_details)
            VALUES (?, ?, ?, ?, ?)
            """, (user_id, action_type, target_id, target_table, details))
        conn.commit()
    except Exception as e:
        print("Audit log error:", e)
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass
