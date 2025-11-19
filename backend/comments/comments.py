import os
from flask_jwt_extended import jwt_required, current_user
from flask import Blueprint, jsonify, request
from database.db_operations import get_shared_documents_by_user, share_document,get_shared_documents_with_user
from database.database import SessionLocal
from database.models import Comment, Document, User, HtmlFile
from sqlalchemy import and_


comments_bp = Blueprint('comments', __name__)



@comments_bp.route('/', methods=['POST'])
@jwt_required()
def create_comment():
    session = SessionLocal()
    try:
        data = request.json
        document_id = data.get('document_id')
        content = data.get('content')
       
        made_by = current_user.id 
        if not document_id or not content:
            return jsonify({'error': 'document_id and content are required'}), 400
        shared_docs = get_shared_documents_with_user(session)
        print("SHARED DOCS:",shared_docs )
        isInvited = False
        for doc in shared_docs:
            if doc['id'] == document_id:
                isInvited = True
                break
        doc = session.query(Document).filter_by(id=document_id).first()
        print("CURRENT USER:",current_user.id, " DOC OWNER:",doc.user_id)
        if doc.user_id == current_user.id:
            print("OWNER ACCESS")
            isInvited = True        
        if not isInvited:
            return jsonify({'error': 'User is not invited to this document'}), 403
        
        
        new_comment = Comment(
            document_id=document_id,
            made_by=made_by,
            content=content
        )
        session.add(new_comment)
        session.commit()
        
        return jsonify({'message': 'Comment created successfully', 'comment_id': new_comment.id}), 201

    except Exception as e:
        session.rollback()
        print(f"Error creating comment: {e}")
        return jsonify({'error': 'Failed to create comment'}), 500

    finally:
        session.close()
@comments_bp.route('/save', methods=['PUT'])
@jwt_required()
def save_comment():
    session = SessionLocal()
    try:
        data = request.json
        document_id = data.get('document_id')
        html_content = data.get('html_content')
        shared_docs = get_shared_documents_with_user(session)
        isInvited = False
        for doc in shared_docs:
            if doc['id'] == document_id:
                isInvited = True
                break
        doc = session.query(Document).filter_by(id=document_id).first()
        print("CURRENT USER:",current_user.id, " DOC OWNER:",doc.user_id)
        if doc.user_id == current_user.id:
            print("OWNER ACCESS")
            isInvited = True
        if not isInvited:
            return jsonify({'error': 'User is not invited to this document'}), 403
        
        html= session.query(HtmlFile).filter_by(doc_id=document_id).one_or_none()
        print("HTML PATH:",html.file_path)
        with open(html.file_path, 'w', encoding='utf-8') as f:
            new_content_size = len(html_content.encode('utf-8'))
            existing_file_size = os.path.getsize(html.file_path)
            print(f"New content size: {new_content_size}, Existing file size: {existing_file_size}")
            if new_content_size > existing_file_size:
                f.write(html_content)
        return jsonify({'message': 'Comment saved successfully'}, 200)
    except Exception as e:
        session.rollback()
        print(f"Error saveing comment: {e}")
        return jsonify({'error': 'Failed to save comment'}), 500


@comments_bp.route('/<string:document_id>', methods=['GET'])
@jwt_required()
def get_comments(document_id):
    session = SessionLocal()
    try:
        document = session.query(Document).filter_by(id=document_id).first()

        if document is None:
            return jsonify({'error': 'Document not found'}), 404

        if document.user_id != current_user.id:
            return jsonify({'error': 'Access denied: You do not own this document'}), 403
        comments = session.query(Comment).filter(Comment.document_id == document_id).all()
        
        comments_list = [{
            'id': str(comment.id),
            'made_by': (session.query(User.username).filter(User.id == comment.made_by).scalar()),
            'content': comment.content,
            'created_at': comment.created_at.isoformat(),
            'resolved': comment.resolved
        } for comment in comments]
        return jsonify(comments_list), 200

    except Exception as e:
        print(f"Error fetching comments: {e}")
        return jsonify({'error': 'Failed to fetch comments'}), 500

    finally:
        session.close()

@comments_bp.route('/resolve', methods=['PUT'])
@jwt_required()
def resolve_comment():
    session = SessionLocal()
    try:
        document_id = request.json.get('document_id')
        comment_id = request.json.get('comment_id')
        print(current_user.id)
        comment = session.query(Comment).join(Document, Comment.document_id == Document.id).filter(Comment.id == comment_id, Comment.document_id == document_id, Document.user_id == current_user.id).one_or_none()
        if not comment:
            return jsonify({'error': 'Comment not found'}), 404

        comment.resolved = True
        session.commit()
        return jsonify({'message': 'Comment resolved successfully'}), 200

    except Exception as e:
        session.rollback()
        print(f"Error resolving comment: {e}")
        return jsonify({'error': 'Failed to resolve comment'}), 500

    finally:
        session.close()