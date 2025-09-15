import click
from werkzeug.security import generate_password_hash
from models import db, User


@click.command("create-admin")
@click.argument("name")
@click.argument("email")
@click.argument("password")
@click.argument("phone")
@click.argument("role")
def create_admin(name, email, password, phone, role):
    """
    Create a normal admin user.
    """
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        click.echo(f"User '{email}' already exists.")
        return

    hashed_password = generate_password_hash(password)
    new_user = User(
        name=name,
        email=email,
        password=hashed_password,
        phone=phone,
        role="admin"
        )
    db.session.add(new_user)
    db.session.commit()
    click.echo(f"Admin '{email}' created successfully.")
