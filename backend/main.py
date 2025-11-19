import os
from flask import Flask, jsonify,request, send_file, send_from_directory,abort
import subprocess
from flask_cors import CORS
from database.db_operations import delete_document,is_owner, fetch_all_documents_for_user, get_other_users,update_docx, get_docx,create_document_for_user,get_html_for_edit,save_html_content
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity, set_access_cookies, unset_jwt_cookies, get_jwt,current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from database.database import Base,engine
from auth.auth import auth_bp
from collab.collab import collab_bp
from comments.comments import comments_bp
from database.models import User
from database.database import SessionLocal
from datetime import datetime, timedelta, timezone



app = Flask(__name__)
app.config['JWT_TOKEN_LOCATION'] = ['cookies']
app.config['JWT_ACCESS_COOKIE_PATH'] = '/'
app.config['JWT_COOKIE_CSRF_PROTECT'] = False
app.config['JWT_COOKIE_DOMAIN'] = 'localhost'

# Set the secret key to sign the JWTs with
app.config['JWT_SECRET_KEY'] = 'super-secret'
jwt = JWTManager(app)
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(collab_bp, url_prefix='/api/collab')
app.register_blueprint(comments_bp, url_prefix='/api/comments')

CORS(app, supports_credentials=True, origins=["http://localhost:5173"])
Base.metadata.create_all(bind=engine)


@app.route('/documents/<user_id>/<doc_id>/<filename>')
def serve_document_image(user_id, doc_id, filename):
    print("Serving image:", doc_id, filename)
    folder = os.path.join('documents', f'{user_id}', doc_id)
    if not os.path.exists(os.path.join(folder, filename)):
        print("File not found:", os.path.join(folder, filename))
        abort(404)
    return send_from_directory(folder, filename)


@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    session = SessionLocal()
    identity = jwt_data["sub"]
    return session.query(User).filter_by(id=identity).one_or_none()
 

@app.after_request
def refresh_expiring_jwts(response):
    try:
        exp_timestamp = get_jwt()["exp"]
        now = datetime.now(timezone.utc)
        target_timestamp = datetime.timestamp(now + timedelta(minutes=30))
        if target_timestamp > exp_timestamp:
            access_token = create_access_token(identity=get_jwt_identity())
            set_access_cookies(response, access_token)
        return response
    except (RuntimeError, KeyError):
        # Case where there is not a valid JWT. Just return the original response
        return response

@app.route('/api/documents', methods=['POST'])
@jwt_required()
def create_document():
    session = SessionLocal()
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part in the request'}), 400

        file = request.files['file']
        if file.filename == '' or not secure_filename(file.filename):
            return jsonify({'error': 'Invalid filename'}), 400
        if not file.filename.lower().endswith('.docx'):
            return jsonify({'error': 'Only .docx files are allowed'}), 400

        data = request.form
        document_name = (
            data.get('document_name') + ".docx"
            if data.get('document_name')
            else secure_filename(file.filename)
        )
        print("FILENAME:", document_name)

        new_doc = create_document_for_user(session, file, document_name)
        session.commit()
        return jsonify(new_doc.to_dict()), 201

    except Exception as e:
        session.rollback()
        print(f"Error creating document: {e}")
        return jsonify({'error': 'Failed to create document'}), 500

    finally:
        session.close()


# -------------------------------
# Save updated HTML content
# -------------------------------
@app.route('/api/documents/<string:doc_id>/save', methods=['PUT'])
@jwt_required()
def save_document(doc_id):
    session = SessionLocal()
    try:
        html_content = request.json.get('html')
        if not html_content:
            return jsonify({'error': 'HTML content is required'}), 400

        success = save_html_content(session, doc_id, html_content)
        if success[1] != 200:
            session.rollback()
            return success

        session.commit()
        return success

    except Exception as e:
        session.rollback()
        print(f"Error saving HTML: {e}")
        return jsonify({'error': 'Failed to save document'}), 500

    finally:
        session.close()


# -------------------------------
# Regenerate DOCX from HTML
# -------------------------------
@app.route('/api/documents/<string:doc_id>/docx', methods=['PUT'])
@jwt_required()
def export_docx(doc_id):
    session = SessionLocal()
    try:
        html_content = request.json.get('html')
        if not html_content:
            return jsonify({'error': 'HTML content is required'}), 400

        success =save_html_content(session, doc_id, html_content)
        if success[1] != 200:
            session.rollback()
            return success
        update_docx(session, doc_id)
        session.commit()

        return jsonify({'message': 'Document updated successfully'}), 200

    except Exception as e:
        session.rollback()
        print(f"Error exporting DOCX: {e}")
        return jsonify({'error': 'Failed to export DOCX'}), 500

    finally:
        session.close()


# -------------------------------
# Get all documents
# -------------------------------
@app.route('/api/documents', methods=['GET'])
@jwt_required()
def get_all_documents():
    session = SessionLocal()
    try:
        documents = fetch_all_documents_for_user(session)
        return jsonify(documents), 200

    except Exception as e:
        print(f"Error fetching documents: {e}")
        return jsonify({'error': 'Failed to fetch documents'}), 500

    finally:
        session.close()


# -------------------------------
# Get HTML version of a document
# -------------------------------
@app.route('/api/documents/<string:doc_id>/html', methods=['GET'])
@jwt_required()
def get_html(doc_id):
    session = SessionLocal()
    try:
        html_content = get_html_for_edit(session, doc_id)
        if html_content is None:
            return jsonify({'error': 'HTML file not found'}), 404
        return html_content, 200

    except Exception as e:
        print(f"Error fetching HTML: {e}")
        return jsonify({'error': 'Failed to fetch HTML'}), 500

    finally:
        session.close()


# -------------------------------
# Download DOCX version
# -------------------------------
@app.route('/api/documents/<string:doc_id>/docx', methods=['GET'])
@jwt_required()
def download_docx(doc_id):
    session = SessionLocal()
    try:
        docx = get_docx(session, doc_id)
        if docx is None:
            return jsonify({'error': 'DOCX file not found'}), 404

        print("File path:", docx.file_path)
        return send_from_directory(
            os.path.dirname(docx.file_path),
            os.path.basename(docx.file_path),
            as_attachment=True
        ), 200

    except Exception as e:
        print(f"Error downloading DOCX: {e}")
        return jsonify({'error': 'Failed to download DOCX'}), 500

    finally:
        session.close()


# -------------------------------
# Delete a document
# -------------------------------
@app.route('/api/documents/<string:doc_id>', methods=['DELETE'])
@jwt_required()
def delete_doc(doc_id):
    session = SessionLocal()
    try:
        success = delete_document(session, doc_id)
        if not success:
            session.rollback()
            return jsonify({'error': 'Document not found or could not be deleted'}), 404

        session.commit()
        return jsonify({'message': 'Document deleted successfully'}), 200

    except Exception as e:
        session.rollback()
        print(f"Error deleting document: {e}")
        return jsonify({'error': 'Failed to delete document'}), 500

    finally:
        session.close()


# -------------------------------
# Get list of all other users
# -------------------------------
@app.route('/api/users', methods=['GET'])
@jwt_required()
def get_all_users():
    session = SessionLocal()
    try:
        users = get_other_users(session)
        users_list = [{'id': str(user.id), 'username': user.username} for user in users]
        return jsonify(users_list), 200

    except Exception as e:
        print(f"Error fetching users: {e}")
        return jsonify({'error': 'Failed to fetch users'}), 500

    finally:
        session.close()

@app.route('/api/isOwner/<string:doc_id>', methods=['GET'])
@jwt_required()
def check_if_owner(doc_id):
    session = SessionLocal()
    try:
        return is_owner(session, doc_id)
    except Exception as e:
        return jsonify({'error': 'Failed to check ownership'}), 500





if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000,debug=True)