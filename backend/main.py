from flask import Flask, jsonify,request
import subprocess
from flask_cors import CORS
from database.db_operations import fetch_all_documents_for_user,create_document_for_user,get_html_for_edit,save_html_content
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity, set_access_cookies, unset_jwt_cookies, get_jwt,current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from database.database import Base,engine
from auth.auth import auth_bp
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

CORS(app, supports_credentials=True, origins=["http://localhost:5173"])
Base.metadata.create_all(bind=engine)


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
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    file = request.files['file']
    if file.filename == '' or not secure_filename(file.filename):
        return jsonify({'error': 'Invalid filename'}), 400
    if not file.filename.lower().endswith('.docx'):
        return jsonify({'error': 'Only .docx files are allowed'}), 400
    data = request.form
    document_name = data.get('document_name') +".docx" if data.get('document_name') else secure_filename(file.filename)
    print("FILENAME:",document_name)
    new_doc = create_document_for_user(file, document_name)
    return jsonify(new_doc.to_dict()), 201

# -------------------------------
# Update the HTML content (regenerate DOCX)
# -------------------------------
@app.route('/api/documents/<string:doc_id>/save', methods=['PUT'])
def update_html(doc_id):
    html_content = request.json.get('html')
    if not html_content:
        return jsonify({'error': 'HTML content is required'}), 400
    # Here you would typically update the document in the database
    save_html_content(doc_id, html_content)
    return jsonify({'message': 'Document updated successfully'}), 200


# -------------------------------
# Update the DOCX directly (optional)
# -------------------------------
@app.route('/api/documents/<string:doc_id>/docx', methods=['PUT'])
def update_docx(doc_id):
    pass


# -------------------------------
# Get all documents (metadata)
# -------------------------------
@app.route('/api/documents', methods=['GET'])
@jwt_required()
def get_all_documents():
    documents = fetch_all_documents_for_user()
    return jsonify([doc.to_dict() for doc in documents])


# -------------------------------
# Get the HTML version of a document
# -------------------------------
@app.route('/api/documents/<string:doc_id>/html', methods=['GET'])
def get_html(doc_id):
    html_content = get_html_for_edit(doc_id)
    if html_content is None:
        return jsonify({'error': 'HTML file not found'}), 404
    return html_content, 200


# -------------------------------
# Download the DOCX version of a document
# -------------------------------
@app.route('/api/documents/<string:doc_id>/docx', methods=['GET'])
def download_docx(doc_id):
    pass


# -------------------------------
# Delete a document
# -------------------------------
@app.route('/api/documents/<string:doc_id>', methods=['DELETE'])
def delete_document(doc_id):
    pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000,debug=True)