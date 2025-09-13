from datetime import date, timedelta
from sqlalchemy import Enum
from database import db
import enum

class RoleEnum(enum.Enum):
    admin = "admin"
    user = "user"

class StatusEnum(enum.Enum):
    active = "active"
    cancelled = "cancelled"
    expired = "expired"

class User(db.Model):
    __tablename__ = "Users"
    UserID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Name = db.Column(db.String(100), nullable=False)
    Email = db.Column(db.String(100), unique=True, nullable=False)
    Role = db.Column(Enum(RoleEnum), default=RoleEnum.user, nullable=False)

class Plan(db.Model):
    __tablename__ = "Plans"
    PlanID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    PlanName = db.Column(db.String(100), nullable=False)
    Description = db.Column(db.Text)
    Price = db.Column(db.Numeric(10,2), nullable=False)
    DataQuota = db.Column(db.Integer)
    Validity = db.Column(db.Integer)  # days

class Subscription(db.Model):
    __tablename__ = "Subscriptions"
    SubscriptionID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    UserID = db.Column(db.Integer, db.ForeignKey("Users.UserID"), nullable=False)
    PlanID = db.Column(db.Integer, db.ForeignKey("Plans.PlanID"), nullable=False)
    StartDate = db.Column(db.Date, default=date.today)
    EndDate = db.Column(db.Date)
    Status = db.Column(Enum(StatusEnum), default=StatusEnum.active, nullable=False)

    user = db.relationship("User", backref="subscriptions")
    plan = db.relationship("Plan", backref="subscriptions")

    def set_end_date(self, validity_days):
        self.EndDate = date.today() + timedelta(days=validity_days)

class Discount(db.Model):
    __tablename__ = "Discounts"
    DiscountID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    PlanID = db.Column(db.Integer, db.ForeignKey("Plans.PlanID"), nullable=False)
    DiscountName = db.Column(db.String(100))
    DiscountPercent = db.Column(db.Numeric(5,2))
    ValidFrom = db.Column(db.Date)
    ValidTo = db.Column(db.Date)

class AuditLog(db.Model):
    __tablename__ = "AuditLogs"
    LogID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    UserID = db.Column(db.Integer, db.ForeignKey("Users.UserID"))
    Action = db.Column(db.String(255))
    ActionTime = db.Column(db.DateTime, default=db.func.now())
