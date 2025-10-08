from flask import Blueprint, app, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from database.models import User
from datetime import datetime
from datetime import timedelta
from datetime import timezone

from flask import Flask
from flask import jsonify

from flask_jwt_extended import create_access_token, unset_jwt_cookies

from flask_jwt_extended import set_access_cookies
from database.database import SessionLocal

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/register", methods=["POST"])
def register():
    session = SessionLocal()
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if session.query(User).filter_by(username=username).first():
        return jsonify({"msg": "User already exists"}), 400
    try:
        new_user = User(username=username, password_hash=generate_password_hash(password))
        session.add(new_user)
        session.commit()
    except Exception as e:
        session.rollback()
        return jsonify({"msg": "Error occurred while registering user"}), 500
    finally:
        session.close()
    return jsonify({"msg": "User registered successfully"}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    
    session = SessionLocal()
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    user = session.query(User).filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"msg": "Invalid username or password"}), 401

    token = create_access_token(identity=user.id)

    # Set the JWT cookies in the response
    resp = jsonify({'login': True})
    set_access_cookies(resp, token)
    return resp, 200

@auth_bp.route('/logout', methods=['POST'])
def logout():
    resp = jsonify({'logout': True})
    unset_jwt_cookies(resp)
    return resp, 200



    
