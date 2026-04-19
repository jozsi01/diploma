from flask import Blueprint, app, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from database.models import User
from datetime import datetime
from datetime import timedelta
from datetime import timezone

from flask import Flask
from flask import jsonify

from flask_jwt_extended import create_access_token, unset_jwt_cookies
import logging
from flask_jwt_extended import set_access_cookies
from database.database import SessionLocal

# Configure logger for this module
logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/register", methods=["POST"])
def register():
    logger.info("Register endpoint was hit")
    session = SessionLocal()
    try:
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")
        
        logger.debug("Registration attempt for username: %s", username)

        if session.query(User).filter_by(username=username).first():
            logger.warning("Registration failed: User already exists for username: %s", username)
            return jsonify({"msg": "User already exists"}), 400
        
        new_user = User(username=username, password_hash=generate_password_hash(password))
        session.add(new_user)
        session.commit()
        logger.info("User registered successfully: %s", username)
        return jsonify({"msg": "User registered successfully"}), 201
        
    except Exception as e:
        session.rollback()
        logger.error("Error occurred while registering user: %s", str(e), exc_info=True)
        return jsonify({"msg": "Error occurred while registering user"}), 500
    finally:
        session.close()


@auth_bp.route('/login', methods=['POST'])
def login():
    logger.info("Login endpoint was hit")
    logger.debug("Login request metadata: remote_addr=%s, content_type=%s", request.remote_addr, request.content_type)

    if not request.is_json:
        logger.warning("Login failed: request body is not JSON")
        return jsonify({"msg": "Request must be JSON"}), 400
    
    session = SessionLocal()
    try:
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")
        
        logger.debug("Login attempt for username: %s", username)
        
        user = session.query(User).filter_by(username=username).first()
        logger.debug("User lookup result: %s", "User found" if user else "User not found")
        
        if not user or not check_password_hash(user.password_hash, password):
            logger.warning("Login failed: Invalid username or password for username: %s", username)
            return jsonify({"msg": "Invalid username or password"}), 401
        
        token = create_access_token(identity=user.id)
        # Set the JWT cookies in the response
        resp = jsonify({'login': True})
        set_access_cookies(resp, token)
        logger.info("User logged in successfully: %s", username)
        return resp, 200
        
    except Exception as e:
        logger.error("Error occurred while logging in: %s", str(e), exc_info=True)
        return jsonify({"msg": "Error occurred while logging in"}), 500
    finally:
        session.close()
        

@auth_bp.route('/logout', methods=['POST'])
def logout():
    logger.info("Logout endpoint was hit")
    resp = jsonify({'logout': True})
    unset_jwt_cookies(resp)
    logger.info("User logged out successfully")
    return resp, 200



    
