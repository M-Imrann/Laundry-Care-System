import re
from utils.exceptions_util import ValidationError
from models import User

# Regex patterns
EMAIL_PATTERN = r"^[\w\.-]+@[\w\.-]+\.\w+$"
PHONE_PATTERN = r"^\+?\d{10,15}$"
PASSWORD_PATTERN = (
    r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)"
    r"(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
)


def validate_email(email: str):
    """
    Validate email format and uniqueness.
    """
    if not re.match(EMAIL_PATTERN, email):
        raise ValidationError("Invalid email format", field="email")

    if User.query.filter_by(email=email).first():
        raise ValidationError("Email already exists", field="email")


def validate_password(password: str):
    """
    Validate password strength.
    Must include:
    - At least 8 characters
    - One uppercase
    - One lowercase
    - One number
    - One special character
    """
    if not re.match(PASSWORD_PATTERN, password):
        raise ValidationError(
            "Password must be at least 8 characters long, include uppercase, "
            "lowercase, number, and special character",
            field="password"
        )


def validate_phone(phone: str):
    """
    Validate phone number format and uniqueness.
    """
    if not re.match(PHONE_PATTERN, phone):
        raise ValidationError("Invalid phone number format", field="phone")

    if User.query.filter_by(phone=phone).first():
        raise ValidationError("Phone number already exists", field="phone")
