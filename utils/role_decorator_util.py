from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, get_jwt
from models import UserRole


def role_required(*roles):
    """
    A decorator to enforce role-based access.
    Usage:
        @role_required("customer")
        @role_required("worker", "admin")
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            identity = get_jwt_identity()
            claims = get_jwt()
            user_role = claims.get("role")

            # Convert roles like "customer" -> UserRole.customer.value
            allowed_roles = []
            for role in roles:
                try:
                    allowed_roles.append(UserRole[role.lower()].value)
                except KeyError:
                    return jsonify({"error": f"Invalid role '{role}'"}), 400

            if user_role not in allowed_roles:
                return jsonify({"error": "Unauthorized"}), 403

            # Inject into function arguments
            return fn(
                *args,
                user_id=int(identity),
                user_role=user_role,
                **kwargs
                )

        return wrapper

    return decorator
