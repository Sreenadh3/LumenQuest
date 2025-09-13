from flask import Blueprint, request, jsonify
from database import db
from models import Plan, AuditLog

plans_bp = Blueprint("plans", __name__)

@plans_bp.route("/plans", methods=["POST"])
def create_plan():
    data = request.json
    plan = Plan(**data)
    db.session.add(plan)
    db.session.commit()
    return jsonify({"message": "Plan created", "plan_id": plan.PlanID})

@plans_bp.route("/plans", methods=["GET"])
def get_plans():
    plans = Plan.query.all()
    return jsonify([{
        "PlanID": p.PlanID, "PlanName": p.PlanName, "Price": float(p.Price),
        "DataQuota": p.DataQuota, "Validity": p.Validity
    } for p in plans])

@plans_bp.route("/plans/<int:plan_id>", methods=["PUT"])
def update_plan(plan_id):
    plan = Plan.query.get(plan_id)
    if not plan:
        return jsonify({"error": "Plan not found"}), 404
    data = request.json
    for key, value in data.items():
        setattr(plan, key, value)
    db.session.commit()
    return jsonify({"message": "Plan updated"})

@plans_bp.route("/plans/<int:plan_id>", methods=["DELETE"])
def delete_plan(plan_id):
    plan = Plan.query.get(plan_id)
    if not plan:
        return jsonify({"error": "Plan not found"}), 404
    db.session.delete(plan)
    db.session.commit()
    return jsonify({"message": "Plan deleted"})
