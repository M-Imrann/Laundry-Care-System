from flask import jsonify
from database import db
from models import User, UserRole, Customer, Worker
from utils.validators_util import (
    validate_email,
    validate_password,
    validate_phone
)
from utils.exceptions_util import (
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError
)
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from datetime import timedelta


def hash_password(password):
    """
    Hash a plain-text password.

    Args:
        password: The plain-text password.

    Returns:
        str: The hashed password.
    """
    return generate_password_hash(password)


def check_password(password, hashed):
    """
    Verify if a plain-text password matches its hash.

    Args:
        password: The plain-text password.
        hashed: The stored hashed password.

    Returns:
        bool: True if the password matches, otherwise False.
    """
    return check_password_hash(hashed, password)


def generate_access_token(user_id, role):
    """
    Generate a JWT access token for a user.

    Args:
        user_id: The ID of the user.
        role: The role of the user.

    Returns:
        str: Encoded JWT token valid for 4 hours.
    """
    return create_access_token(
        identity=str(user_id),   # must be string
        additional_claims={"role": role},
        expires_delta=timedelta(hours=4)
    )


def create_user(auth_payload):
    """
    Create a new user and assign them a role (customer or worker).

    Args:
        auth_payload: JSON payload containing user details
        (name, email, phone, password, and role).

    Returns:
        Response: JSON response with success message, created user ID,
        and role, or error details if validation fails.
    """
    try:
        name = auth_payload["name"]
        email = validate_email(auth_payload["email"])
        phone = validate_phone(auth_payload["phone"])
        role = auth_payload["role"]
        password = validate_password(auth_payload["password"])

        # Map role string to UserRole enum
        try:
            role_enum = UserRole[role.lower()]
        except KeyError:
            raise ValidationError("Invalid role provided", field="role")

        # Create user
        new_user = User(
            name=name,
            email=email,
            password=hash_password(password),
            phone=phone,
            role=role_enum,
        )
        db.session.add(new_user)
        db.session.flush()

        # If user is a customer, create customer profile
        if role_enum == UserRole.customer:
            new_customer = Customer(id=new_user.id)
            db.session.add(new_customer)
        else:
            new_worker = Worker(id=new_user.id)
            db.session.add(new_worker)

        db.session.commit()

        return jsonify({
            "message": "User created successfully",
            "user_id": new_user.id,
            "role": role_enum.value
        }), 201

    except ValidationError as e:
        db.session.rollback()
        return jsonify(e.to_dict()), 400

    except (AuthenticationError, AuthorizationError) as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 403

    except NotFoundError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 404

    except Exception as e:
        db.session.rollback()
        return jsonify(
            {"error": "Internal server error", "details": str(e)}
        ), 500


def login_user(email, password):
    """
    Authenticate a user by verifying email and password,
    then generate a JWT access token.

    Args:
        email: The user's email.
        password: The user's plain-text password.

    Returns:
        Response: JSON response with success message, access token,
        and basic user details if valid. Otherwise, returns an error.
    """
    # Check if user exists
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "Invalid email"}), 401

    # Verify password
    if not check_password(password, user.password):
        return jsonify({"error": "Invalid password"}), 401

    # Generate token
    token = generate_access_token(user.id, user.role.value)

    return jsonify({
        "message": "Login successful",
        "access_token": token,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role.value
        }
    }), 200
