from werkzeug.security import generate_password_hash
from flask import jsonify
from database import db
from models import (
    User,
    Worker,
    Customer,
    Order,
    OrderStatus,
    UserRole
)
from utils.exceptions_util import ValidationError, NotFoundError


def list_all_orders():
    """
    Retrieve and return a list of all orders.

    Returns:
        Response: JSON response with order details including
        order ID, customer ID, worker ID, pickup and delivery times,
        status, price, and cancellation fee.
    """
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return jsonify([
        {
            "order_id": order.id,
            "customer_id": order.customer_id,
            "worker_id": order.worker_id,
            "pickup_time": order.pickup_time.isoformat(),
            "delivery_time": order.delivery_time.isoformat(),
            "status": order.status.value,
            "price": order.price,
            "cancellation_fee": order.cancellation_fee
        } for order in orders
    ]), 200


def create_order_for_customer(
        customer_id,
        worker_id,
        pickup_time,
        delivery_time,
        price,
        created_by,
        address_id
        ):
    """
    Create a new order for a specific customer.

    Args:
        customer_id: The customer placing the order.
        worker_id: The worker assigned to fulfill the order.
        pickup_time: The scheduled pickup time.
        delivery_time: The scheduled delivery time.
        price: The order price.
        created_by: The ID of the admin creating the order.
        address_id: The associated address ID.

    Raises:
        ValidationError: If delivery time is earlier than or
            equal to pickup time.

    Returns:
        Response: JSON response confirming order creation
           with the new order ID.
    """
    if delivery_time <= pickup_time:
        raise ValidationError("Delivery time must be after pickup time")

    new_order = Order(
        customer_id=customer_id,
        worker_id=worker_id,
        pickup_time=pickup_time,
        delivery_time=delivery_time,
        status=OrderStatus.created,
        price=price,
        created_by=created_by,
        address_id=address_id
    )
    db.session.add(new_order)
    db.session.commit()

    return jsonify(
        {
            "message": "Order created by admin",
            "order_id": new_order.id
        }
    ), 201


def add_worker(name, email, phone, password):
    """
    Add a new worker to the system.

    Args:
        name: Worker's name.
        email: Worker's email.
        phone: Worker's phone number.
        password: Worker's account password.

    Returns:
        Response: JSON response confirming worker creation with worker ID.
    """
    hashed_pw = generate_password_hash(password)
    new_worker = User(
        name=name,
        email=email,
        password=hashed_pw,
        phone=phone,
        role=UserRole.worker
    )
    db.session.add(new_worker)
    db.session.flush()
    worker_profile = Worker(id=new_worker.id)
    db.session.add(worker_profile)
    db.session.commit()

    return jsonify(
        {
            "message": "Worker added successfully",
            "worker_id": new_worker.id
        }
    ), 201


def assign_customer_to_worker(worker_id, customer_id):
    """
    Assign a customer to a specific worker.

    Args:
        worker_id: The worker to assign the customer to.
        customer_id: The customer being assigned.

    Raises:
        NotFoundError: If the customer does not exist.

    Returns:
        Response: JSON response confirming the assignment.
    """
    customer = Customer.query.filter_by(id=customer_id).first()
    if not customer:
        raise NotFoundError("Customer not found")

    customer.assigned_worker_id = worker_id
    db.session.commit()

    return jsonify(
        {
            "message": f"Customer {customer_id} assigned to worker {worker_id}"
        }
    ), 200


def create_admin(name, email, password, phone, role):
    """
    Create a new admin user in the system.

    Args:
        name: Admin's name.
        email: Admin's email.
        password: Admin's account password.
        phone: Admin's phone number.
        role: Role assigned to the new user (should be 'admin').

    Returns:
        Response: JSON response confirming admin creation
        or error if the user already exists.
    """
    if not email or not password:
        return {"error": "email and password are required"}, 400

    # Check if user already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return {"error": "User already exists"}, 400

    # Hash password
    hashed_password = generate_password_hash(password)

    # Create admin in users table
    new_admin = User(
        name=name,
        email=email,
        password=hashed_password,
        phone=phone,
        role=role
    )
    db.session.add(new_admin)
    db.session.commit()

    return {"message": f"Admin '{email}' created successfully"}, 201
