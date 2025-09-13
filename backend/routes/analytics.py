from flask import Blueprint, jsonify
from database import db
from models import Subscription, Plan, StatusEnum
from sqlalchemy import func

analytics_bp = Blueprint("analytics", __name__)

@analytics_bp.route("/analytics/top-plans", methods=["GET"])
def top_plans():
    results = db.session.query(
        Plan.PlanName, func.count(Subscription.SubscriptionID).label("count")
    ).join(Subscription).filter(Subscription.Status == StatusEnum.active).group_by(Plan.PlanID).all()
    return jsonify([{"Plan": r[0], "ActiveSubscriptions": r[1]} for r in results])

@analytics_bp.route("/analytics/trends", methods=["GET"])
def subscription_trends():
    results = db.session.query(
        Subscription.Status, func.count(Subscription.SubscriptionID)
    ).group_by(Subscription.Status).all()
    return jsonify({status.value: count for status, count in results})
