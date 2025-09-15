from flask import Flask
from database import db
from core.config import Config
from flask_jwt_extended import JWTManager

# Routers
from routers.auth_routes import auth_bp
from routers.customer_routes import customer_bp
from routers.worker_routes import worker_bp
from routers.admin_routes import admin_bp
from admin_command import create_admin


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Database
    db.init_app(app)

    # JWT Setup
    JWTManager(app)

    # Register Blueprints
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(customer_bp, url_prefix="/customer")
    app.register_blueprint(worker_bp, url_prefix="/worker")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    app.cli.add_command(create_admin)

    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
