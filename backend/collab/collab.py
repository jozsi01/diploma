from flask_jwt_extended import jwt_required
from flask import Blueprint, request
from database.db_operations import get_shared_documents_by_user, share_document,get_shared_documents_with_user,unshare_document
from database.database import SessionLocal

collab_bp = Blueprint('collab', __name__)


@collab_bp.route('/share', methods=['POST'])
@jwt_required()
def share_document_with_user():
    session = SessionLocal()
    data = request.json
    try:
        document_id = data.get("document_id")
        invited_user_id = data.get("invited_user_id")

        if not document_id or not invited_user_id:
            return {"error": "Missing document_id or invited_user_id"}, 400

        res = share_document(session, document_id, invited_user_id)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error sharing document: {e}")
        return {"error": "Failed to share document"}, 500
    finally:
        session.close()
    return res

@collab_bp.route('/shared_documents/with_user', methods=['GET'])
@jwt_required()
def get_shared():
    session = SessionLocal()
    try:
        shared_docs = get_shared_documents_with_user(session)
        return { "shared_documents": shared_docs }, 200
    finally:
        session.close()
    


@collab_bp.route('/shared_documents/by_user', methods=['GET'])
@jwt_required()
def get_shared_by_user():
    # Logic to retrieve shared documents for the current user
    session = SessionLocal()
    try:
        shared_docs = get_shared_documents_by_user(session)
        return { "shared_documents": shared_docs }, 200
    finally:
        session.close()

@collab_bp.route('/unshare', methods=['POST'])
@jwt_required()
def remove_sharing_document_with_user():
    session = SessionLocal()
    data = request.json
    try:
        document_id = data.get("document_id")
        invited_user_id = data.get("invited_user_id")
        
        if not document_id or not invited_user_id:
            return {"error": "Missing document_id or invited_user_id"}, 400

        res = unshare_document(session, document_id, invited_user_id)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error unsharing document: {e}")
        return {"error": "Failed to unshare document"}, 500
    finally:
        session.close()
    return res