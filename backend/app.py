# app.py
from flask import Flask, request, jsonify, g
from db import get_connection
from utils import hash_password, verify_password, generate_jwt, auth_required, admin_required, write_audit
import pyodbc
from datetime import datetime, timedelta
import os

app = Flask(__name__)

# ---------------------------
# Auth: signup & login
# ---------------------------
@app.route("/auth/signup", methods=["POST"])
def signup():
    data = request.json or {}
    full_name = data.get("full_name")
    email = data.get("email")
    phone = data.get("phone_number")
    role = data.get("role", "END_USER")  # END_USER or ADMIN
    username = data.get("username")
    password = data.get("password")

    if not (full_name and email and username and password):
        return jsonify({"error": "missing required fields"}), 400

    pwd_hash = hash_password(password)

    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        # Insert into Users
        cur.execute("INSERT INTO Users (full_name, email, phone_number, role) VALUES (?, ?, ?, ?)",
                    (full_name, email, phone, role))
        conn.commit()

        # get user_id
        cur.execute("SELECT SCOPE_IDENTITY()")
        user_id_row = cur.fetchone()
        user_id = user_id_row[0] if user_id_row else None


        # Insert login
        cur.execute("INSERT INTO User_Logins (user_id, username, password_hash) VALUES (?, ?, ?)",
                    (user_id, username, pwd_hash))
        conn.commit()

        write_audit(user_id, "CREATE_USER", target_id=user_id, target_table="Users", details=f"role={role}")

        return jsonify({"message": "signup successful", "user_id": user_id}), 201
    except pyodbc.IntegrityError as e:
        return jsonify({"error": "user or username/email already exists", "details": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "internal error", "details": str(e)}), 500
    finally:
        if conn:
            cur.close()
            conn.close()

@app.route("/auth/login", methods=["POST"])
def login():
    data = request.json or {}
    username = data.get("username")
    password = data.get("password")
    if not (username and password):
        return jsonify({"error": "missing username or password"}), 400

    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT login_id, user_id, password_hash FROM User_Logins WHERE username = ?", (username,))
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "invalid credentials"}), 401
        login_id, user_id, password_hash = row

        if not verify_password(password, password_hash):
            return jsonify({"error": "invalid credentials"}), 401

        # get user details
        cur.execute("SELECT full_name, email, role FROM Users WHERE user_id = ?", (user_id,))
        ur = cur.fetchone()
        full_name, email, role = ur

        # update last_login
        cur.execute("UPDATE User_Logins SET last_login = ? WHERE login_id = ?", (datetime.utcnow(), login_id))
        conn.commit()

        payload = {
            "user_id": int(user_id),
            "username": username,
            "full_name": full_name,
            "email": email,
            "role": role
        }
        token = generate_jwt(payload)

        write_audit(user_id, "LOGIN", details=f"username={username}")

        return jsonify({"token": token, "user": payload}), 200

    except Exception as e:
        return jsonify({"error": "internal error", "details": str(e)}), 500
    finally:
        if conn:
            cur.close()
            conn.close()

# ---------------------------
# Plans endpoints
# ---------------------------
@app.route("/plans", methods=["GET"])
def list_plans():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT plan_id, name, description, type, monthly_price, monthly_quota_gb, is_active FROM Plans WHERE is_active = 1")
    rows = cur.fetchall()
    plans = []
    for r in rows:
        plans.append({
            "plan_id": int(r[0]),
            "name": r[1],
            "description": r[2],
            "type": r[3],
            "monthly_price": float(r[4]),
            "monthly_quota_gb": int(r[5]),
            "is_active": bool(r[6])
        })
    cur.close()
    conn.close()
    return jsonify(plans), 200

@app.route("/plans", methods=["POST"])
@admin_required
def create_plan():
    data = request.json or {}
    name = data.get("name")
    description = data.get("description")
    ptype = data.get("type", "OTHER")
    price = data.get("monthly_price")
    quota = data.get("monthly_quota_gb", 0)
    is_active = 1 if data.get("is_active", True) else 0
    created_by = g.user["user_id"]

    if not (name and price is not None):
        return jsonify({"error": "missing fields"}), 400

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO Plans (name, description, type, monthly_price, monthly_quota_gb, is_active, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (name, description, ptype, price, quota, is_active, created_by))
    conn.commit()
    cur.execute("SELECT SCOPE_IDENTITY()")
    plan_id = int(cur.fetchone()[0])
    write_audit(created_by, "CREATE_PLAN", target_id=plan_id, target_table="Plans", details=f"name={name}")
    cur.close()
    conn.close()
    return jsonify({"message": "plan created", "plan_id": plan_id}), 201

@app.route("/plans/<int:plan_id>", methods=["PUT"])
@admin_required
def update_plan(plan_id):
    data = request.json or {}
    fields = []
    params = []
    allowed = ["name", "description", "type", "monthly_price", "monthly_quota_gb", "is_active"]
    for k in allowed:
        if k in data:
            fields.append(f"{k} = ?")
            params.append(data[k])
    if not fields:
        return jsonify({"error": "no fields to update"}), 400
    params.append(plan_id)
    conn = get_connection()
    cur = conn.cursor()
    sql = f"UPDATE Plans SET {', '.join(fields)}, updated_at = GETDATE() WHERE plan_id = ?"
    cur.execute(sql, params)
    conn.commit()
    write_audit(g.user['user_id'], "UPDATE_PLAN", target_id=plan_id, target_table="Plans", details=str(data))
    cur.close()
    conn.close()
    return jsonify({"message": "plan updated"}), 200

@app.route("/plans/<int:plan_id>", methods=["DELETE"])
@admin_required
def delete_plan(plan_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE Plans SET is_active = 0, updated_at = GETDATE() WHERE plan_id = ?", (plan_id,))
    conn.commit()
    write_audit(g.user['user_id'], "DELETE_PLAN", target_id=plan_id, target_table="Plans")
    cur.close()
    conn.close()
    return jsonify({"message": "plan deactivated"}), 200

# ---------------------------
# Discounts (admin)
# ---------------------------
@app.route("/discounts", methods=["POST"])
@admin_required
def create_discount():
    data = request.json or {}
    name = data.get("name")
    description = data.get("description")
    discount_percent = data.get("discount_percent")
    start_date = data.get("start_date")
    end_date = data.get("end_date")
    created_by = g.user["user_id"]

    if not all([name, discount_percent, start_date, end_date]):
        return jsonify({"error": "missing fields"}), 400

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO Discounts (name, description, discount_percent, start_date, end_date, created_by)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, description, discount_percent, start_date, end_date, created_by))
    conn.commit()
    cur.execute("SELECT SCOPE_IDENTITY()")
    discount_id = int(cur.fetchone()[0])
    write_audit(created_by, "CREATE_DISCOUNT", target_id=discount_id, target_table="Discounts", details=name)
    cur.close()
    conn.close()
    return jsonify({"message": "discount created", "discount_id": discount_id}), 201

@app.route("/discounts/apply", methods=["POST"])
@admin_required
def apply_discount_to_plan():
    data = request.json or {}
    plan_id = data.get("plan_id")
    discount_id = data.get("discount_id")
    if not (plan_id and discount_id):
        return jsonify({"error": "missing fields"}), 400
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO Plan_Discounts (plan_id, discount_id) VALUES (?, ?)", (plan_id, discount_id))
    conn.commit()
    write_audit(g.user['user_id'], "UPDATE_DISCOUNT", target_id=plan_id, target_table="Plans", details=f"discount_id={discount_id}")
    cur.close()
    conn.close()
    return jsonify({"message": "discount applied to plan"}), 200

# ---------------------------
# Subscriptions
# ---------------------------
@app.route("/subscriptions/subscribe", methods=["POST"])
@auth_required
def subscribe():
    data = request.json or {}
    user_id = g.user["user_id"]
    plan_id = data.get("plan_id")
    duration_days = int(data.get("duration_days", 30))
    auto_renew = data.get("auto_renew", True)
    discount_id = data.get("discount_id", None)

    if not plan_id:
        return jsonify({"error": "plan_id required"}), 400

    start_date = datetime.utcnow().date()
    end_date = start_date + timedelta(days=duration_days)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO Subscriptions (user_id, plan_id, start_date, end_date, status, auto_renew, discount_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, plan_id, start_date, end_date, "ACTIVE", 1 if auto_renew else 0, discount_id))
    conn.commit()
    cur.execute("SELECT SCOPE_IDENTITY()")
    subscription_id = int(cur.fetchone()[0])
    write_audit(user_id, "SUBSCRIBE", target_id=subscription_id, target_table="Subscriptions", details=f"plan_id={plan_id}")
    cur.close()
    conn.close()
    return jsonify({"message": "subscribed", "subscription_id": subscription_id}), 201

@app.route("/subscriptions/<int:subscription_id>/cancel", methods=["POST"])
@auth_required
def cancel_subscription(subscription_id):
    user_id = g.user["user_id"]
    conn = get_connection()
    cur = conn.cursor()
    # check ownership (admin can cancel any --- but here only owner)
    cur.execute("SELECT user_id FROM Subscriptions WHERE subscription_id = ?", (subscription_id,))
    row = cur.fetchone()
    if not row:
        return jsonify({"error": "subscription not found"}), 404
    owner_id = row[0]
    if owner_id != user_id and g.user.get("role") != "ADMIN":
        return jsonify({"error": "not authorized"}), 403

    cur.execute("UPDATE Subscriptions SET status = ?, updated_at = GETDATE() WHERE subscription_id = ?", ("CANCELLED", subscription_id))
    conn.commit()
    write_audit(user_id, "CANCEL", target_id=subscription_id, target_table="Subscriptions")
    cur.close()
    conn.close()
    return jsonify({"message": "subscription cancelled"}), 200

@app.route("/subscriptions", methods=["GET"])
@auth_required
def list_user_subscriptions():
    user_id = g.user["user_id"]
    # admin can request all with ?all=true
    show_all = request.args.get("all", "false").lower() == "true"
    conn = get_connection()
    cur = conn.cursor()
    if show_all and g.user.get("role") == "ADMIN":
        cur.execute("""
            SELECT s.subscription_id, s.user_id, s.plan_id, s.start_date, s.end_date, s.status
            FROM Subscriptions s
            ORDER BY s.created_at DESC
        """)
    else:
        cur.execute("""
            SELECT s.subscription_id, s.user_id, s.plan_id, s.start_date, s.end_date, s.status
            FROM Subscriptions s
            WHERE s.user_id = ?
            ORDER BY s.created_at DESC
        """, (user_id,))
    rows = cur.fetchall()
    result = []
    for r in rows:
        result.append({
            "subscription_id": int(r[0]),
            "user_id": int(r[1]),
            "plan_id": int(r[2]),
            "start_date": str(r[3]),
            "end_date": str(r[4]) if r[4] else None,
            "status": r[5]
        })
    cur.close()
    conn.close()
    return jsonify(result), 200

# Upgrade / Downgrade (simple approach: create new subscription and mark old)
@app.route("/subscriptions/<int:subscription_id>/change", methods=["POST"])
@auth_required
def change_subscription(subscription_id):
    user_id = g.user["user_id"]
    new_plan_id = request.json.get("new_plan_id")
    reason = request.json.get("reason", "")
    if not new_plan_id:
        return jsonify({"error": "new_plan_id required"}), 400

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id, status FROM Subscriptions WHERE subscription_id = ?", (subscription_id,))
    row = cur.fetchone()
    if not row:
        return jsonify({"error": "subscription not found"}), 404
    owner_id, status = row
    if owner_id != user_id and g.user.get("role") != "ADMIN":
        return jsonify({"error": "not authorized"}), 403

    # mark old as UPGRADED or DOWNGRADED (simple heuristic)
    # compare quotas: get current plan quota and new plan quota
    cur.execute("SELECT monthly_quota_gb FROM Plans WHERE plan_id = ?", (new_plan_id,))
    new_quota_row = cur.fetchone()
    if not new_quota_row:
        return jsonify({"error": "new plan not found"}), 404
    new_quota = int(new_quota_row[0])

    cur.execute("SELECT p.monthly_quota_gb FROM Plans p JOIN Subscriptions s ON s.plan_id = p.plan_id WHERE s.subscription_id = ?", (subscription_id,))
    old_row = cur.fetchone()
    old_quota = int(old_row[0]) if old_row else 0

    change_type = "UPGRADED" if new_quota > old_quota else "DOWNGRADED"

    cur.execute("UPDATE Subscriptions SET status = ?, updated_at = GETDATE() WHERE subscription_id = ?", (change_type, subscription_id))
    # create new subscription starting today
    start_date = datetime.utcnow().date()
    end_date = start_date + timedelta(days=30)
    cur.execute("""
        INSERT INTO Subscriptions (user_id, plan_id, start_date, end_date, status, auto_renew)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (owner_id, new_plan_id, start_date, end_date, "ACTIVE", 1))
    conn.commit()
    cur.execute("SELECT SCOPE_IDENTITY()")
    new_sub_id = int(cur.fetchone()[0])
    write_audit(user_id, change_type, target_id=new_sub_id, target_table="Subscriptions", details=f"old_sub={subscription_id}, reason={reason}")
    cur.close()
    conn.close()
    return jsonify({"message": f"subscription {change_type.lower()}", "new_subscription_id": new_sub_id}), 200

# ---------------------------
# Notifications
# ---------------------------
@app.route("/notifications", methods=["GET"])
@auth_required
def list_notifications():
    user_id = g.user["user_id"]
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT notification_id, message, type, is_read, created_at FROM Notifications WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    rows = cur.fetchall()
    notes = []
    for r in rows:
        notes.append({
            "notification_id": int(r[0]),
            "message": r[1],
            "type": r[2],
            "is_read": bool(r[3]),
            "created_at": str(r[4])
        })
    cur.close()
    conn.close()
    return jsonify(notes), 200

@app.route("/notifications/push", methods=["POST"])
@admin_required
def push_notification():
    data = request.json or {}
    target_user = data.get("user_id")
    message = data.get("message")
    ntype = data.get("type", "SYSTEM")
    if not (target_user and message):
        return jsonify({"error": "user_id and message required"}), 400
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO Notifications (user_id, message, type) VALUES (?, ?, ?)", (target_user, message, ntype))
    conn.commit()
    cur.close()
    conn.close()
    write_audit(g.user['user_id'], "SEND_NOTIFICATION", target_id=target_user, target_table="Notifications", details=message)
    return jsonify({"message": "notification sent"}), 201

# ---------------------------
# Analytics (admin)
# ---------------------------
@app.route("/analytics/top-plans", methods=["GET"])
@admin_required
def top_plans():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.plan_id, p.name, COUNT(s.subscription_id) AS subscribers
        FROM Plans p
        LEFT JOIN Subscriptions s ON s.plan_id = p.plan_id AND s.status = 'ACTIVE'
        GROUP BY p.plan_id, p.name
        ORDER BY subscribers DESC
    """)
    rows = cur.fetchall()
    out = []
    for r in rows:
        out.append({"plan_id": int(r[0]), "name": r[1], "subscribers": int(r[2])})
    cur.close()
    conn.close()
    return jsonify(out), 200

# ---------------------------
# Audit logs (admin)
# ---------------------------
@app.route("/audit-logs", methods=["GET"])
@admin_required
def get_audit_logs():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT log_id, user_id, action_type, target_id, target_table, action_details, created_at FROM Audit_Logs ORDER BY created_at DESC")
    rows = cur.fetchall()
    logs = []
    for r in rows:
        logs.append({
            "log_id": int(r[0]),
            "user_id": int(r[1]),
            "action_type": r[2],
            "target_id": r[3],
            "target_table": r[4],
            "action_details": r[5],
            "created_at": str(r[6])
        })
    cur.close()
    conn.close()
    return jsonify(logs), 200

# ---------------------------
# Simple health check
# ---------------------------
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    # optionally set FLASK_ENV=development
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
