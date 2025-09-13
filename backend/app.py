from flask import Flask
from database import db
from routes.users import users_bp
from routes.plans import plans_bp
from routes.subscriptions import subs_bp
from routes.analytics import analytics_bp
from flask_cors import CORS


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:password@localhost/subscription_db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

CORS(app)

db.init_app(app)

app.register_blueprint(users_bp)
app.register_blueprint(plans_bp)
app.register_blueprint(subs_bp)
app.register_blueprint(analytics_bp)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
