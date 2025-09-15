from flask import Blueprint, request, jsonify
from services.auth_service import create_user, login_user

# Blueprint for authentication-related routes
auth_bp = Blueprint("auth_bp", __name__)


@auth_bp.route("/signup", methods=["POST"])
def signup():
    """
    Register a new user account.

    Returns:
        JSON response with success or error message from the service layer.
    """
    data = request.json or {}
    if not data:
        return jsonify(
            {"error": "Input Payload is required"}
        ), 400

    # Delegate actual creation logic to auth service
    created_user = create_user(data)

    return created_user


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Authenticate a user and return a JWT token.

    Returns:
        JSON response with JWT token if authentication is successful,
        otherwise an error message.
    """
    data = request.json or {}

    email = data.get("email")
    password = data.get("password")

    # Validate required fields
    required_fields = {
        "email": email,
        "password": password,
    }
    for field, value in required_fields.items():
        if not value:
            return jsonify(
                {
                    "error": f"{field.capitalize()} is required",
                    "field": field
                }
            ), 400

    # Delegate login logic to auth service
    return login_user(email=email, password=password)
