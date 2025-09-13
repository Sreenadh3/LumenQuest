from flask import Blueprint, request, jsonify
from database import db
from models import Subscription, Plan, StatusEnum

subs_bp = Blueprint("subscriptions", __name__)

@subs_bp.route("/subscriptions", methods=["POST"])
def subscribe():
    data = request.json
    plan = Plan.query.get(data["PlanID"])
    if not plan:
        return jsonify({"error": "Invalid plan"}), 400
    
    sub = Subscription(UserID=data["UserID"], PlanID=plan.PlanID)
    sub.set_end_date(plan.Validity)
    db.session.add(sub)
    db.session.commit()
    return jsonify({"message": "Subscription created", "subscription_id": sub.SubscriptionID})

@subs_bp.route("/subscriptions/<int:user_id>", methods=["GET"])
def get_user_subs(user_id):
    subs = Subscription.query.filter_by(UserID=user_id).all()
    return jsonify([{
        "SubscriptionID": s.SubscriptionID,
        "PlanID": s.PlanID,
        "Status": s.Status.value,
        "StartDate": str(s.StartDate),
        "EndDate": str(s.EndDate)
    } for s in subs])

@subs_bp.route("/subscriptions/<int:sub_id>/cancel", methods=["PUT"])
def cancel_subscription(sub_id):
    sub = Subscription.query.get(sub_id)
    if not sub:
        return jsonify({"error": "Subscription not found"}), 404
    sub.Status = StatusEnum.cancelled
    db.session.commit()
    return jsonify({"message": "Subscription cancelled"})

@subs_bp.route("/subscriptions/<int:sub_id>/renew", methods=["PUT"])
def renew_subscription(sub_id):
    sub = Subscription.query.get(sub_id)
    if not sub:
        return jsonify({"error": "Subscription not found"}), 404
    sub.set_end_date(sub.plan.Validity)
    db.session.commit()
    return jsonify({"message": "Subscription renewed", "new_end": str(sub.EndDate)})

@subs_bp.route("/subscriptions/<int:sub_id>/upgrade", methods=["PUT"])
def upgrade_subscription(sub_id):
    data = request.json
    sub = Subscription.query.get(sub_id)
    if not sub:
        return jsonify({"error": "Subscription not found"}), 404
    sub.PlanID = data["NewPlanID"]
    sub.set_end_date(sub.plan.Validity)
    db.session.commit()
    return jsonify({"message": "Subscription upgraded"})

@subs_bp.route("/subscriptions/<int:sub_id>/downgrade", methods=["PUT"])
def downgrade_subscription(sub_id):
    data = request.json
    sub = Subscription.query.get(sub_id)
    if not sub:
        return jsonify({"error": "Subscription not found"}), 404
    sub.PlanID = data["NewPlanID"]
    sub.set_end_date(sub.plan.Validity)
    db.session.commit()
    return jsonify({"message": "Subscription downgraded"})
