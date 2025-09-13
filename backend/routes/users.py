from flask import Blueprint, request, jsonify
from database import db
from models import User, AuditLog

users_bp = Blueprint("users", __name__)

@users_bp.route("/users", methods=["POST"])
def create_user():
    data = request.json
    user = User(Name=data["Name"], Email=data["Email"], Role=data.get("Role", "user"))
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "User created", "user_id": user.UserID})

@users_bp.route("/users", methods=["GET"])
def get_users():
    users = User.query.all()
    return jsonify([{
        "UserID": u.UserID, "Name": u.Name, "Email": u.Email, "Role": u.Role.value
    } for u in users])
