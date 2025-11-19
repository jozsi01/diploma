import os
import uuid
import shutil
import subprocess
from io import BytesIO

from flask import jsonify
from flask_jwt_extended import current_user
from database.models import Document, HtmlFile, User, SharedDocument
from sqlalchemy import and_
from html_management import format_image_srcs


BACKEND_PATH = os.getenv("BACKEND_ADDR", "http://localhost:5000/")
# -------------------------------------------------------
# Fetch all documents for the current user
# -------------------------------------------------------
def fetch_all_documents_for_user(session):
    print("Current User in DB Operation:", current_user)
    documents = session.query(Document).filter_by(user_id=current_user.id).all()
    return [doc.to_dict() for doc in documents]


# -------------------------------------------------------
# Convert a file between formats (e.g., DOCX → HTML)
# -------------------------------------------------------
def convert_file(file, filename, input_format, output_format,cwd=os.getcwd()):
    if hasattr(file, 'read'):
        file.seek(0)
        content = file.read()
    else:
        content = file

    filename = filename.rsplit('.', 1)[0]
    print("Temp path: ",f"{cwd}/temp.{input_format}")
    with open(f"{cwd}/temp.{input_format}", "wb") as f:
        f.write(content)

    try:
        # Convert to intermediate ODT first
        first_conv = subprocess.run([
            'soffice', '--headless', '--convert-to', 'odt', f'temp.{input_format}'
        ], check=True, text=True, capture_output=True,cwd=cwd)


        # Convert from ODT to desired format
        second_conv = subprocess.run([
            'soffice', '--headless', '--convert-to', f'{output_format}', 'temp.odt'
        ], check=True, text=True, capture_output=True,cwd=cwd)

        print("Conversion output:", first_conv.stdout, second_conv.stdout)
        print("Conversion errors:", first_conv.stderr, second_conv.stderr)

        with open(f'{cwd}/temp.{output_format}', 'rb') as f:
            converted_content = f.read()
            return converted_content, f'{filename}.{output_format}'
    except subprocess.CalledProcessError as e:
        print("Error during conversion:", e)
        return None, None
    finally:
        if hasattr(file, 'seek'):
            file.seek(0)
        for ext in [input_format, 'odt', output_format]:
            if os.path.exists(f'{cwd}/temp.{ext}'):
                os.remove(f'{cwd}/temp.{ext}')


# -------------------------------------------------------
# Save document file to disk
# -------------------------------------------------------
def save_document(file, filename, doc_id):
    user_folder = os.path.join('documents', f'user_{str(current_user.id)[:4]}', str(doc_id))
    os.makedirs(user_folder, exist_ok=True)

    file_path = os.path.join(user_folder, filename)
    with open(file_path, 'wb') as f:
        f.write(file)
    return file_path


# -------------------------------------------------------
# Create a new document and HTML version for user
# -------------------------------------------------------
def create_document_for_user(session, file, filename):
    doc_id = uuid.uuid4()
    html_id = uuid.uuid4()

   
    path = save_document(file.read(), filename, doc_id)
    html_file, html_filename = convert_file(file, filename, 'docx', 'html',os.path.dirname(path))

    html_file = format_image_srcs(html_file, base_url=BACKEND_PATH + os.path.dirname(path))
    path_html = save_document(html_file, html_filename, doc_id)

    new_document = Document(
        id=doc_id,
        user_id=current_user.id,
        file_name=filename,
        file_path=path
    )
    new_html = HtmlFile(
        id=html_id,
        doc_id=doc_id,
        file_name=html_filename,
        file_path=path_html,
        user_id=current_user.id
    )

    session.add(new_document)
    session.add(new_html)
    session.commit()
    session.refresh(new_document)
    return new_document


# -------------------------------------------------------
# Get HTML content for editing
# -------------------------------------------------------
def get_html_for_edit(session, doc_id):
    html_file_path = session.query(HtmlFile.file_path).filter_by(doc_id=doc_id).one_or_none()
    if not html_file_path:
        return None

    with open(html_file_path[0], 'r', encoding='utf-8') as f:
        return f.read()


# -------------------------------------------------------
# Save edited HTML content
# -------------------------------------------------------
def save_html_content(session, doc_id, html_content):
    html= session.query(HtmlFile).filter_by(doc_id=doc_id).one_or_none()
    print("Curent User in Save HTML:", current_user)
    print("HTML User ID:", html.user_id if html else "No HTML found")
    if html.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    if not html:
        return jsonify({'error': 'HTML file not found'}), 404

    print("HTML File Path:", html.file_path)
    with open(html.file_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    return jsonify({'message': 'Document updated successfully'}), 200


# -------------------------------------------------------
# Retrieve a DOCX document
# -------------------------------------------------------
def get_docx(session, doc_id):
    return session.query(Document).filter_by(id=doc_id, user_id=current_user.id).one_or_none()


# -------------------------------------------------------
# Update DOCX from latest HTML
# -------------------------------------------------------
def update_docx(session, doc_id):
    html = session.query(HtmlFile).filter_by(doc_id=doc_id, user_id=current_user.id).one_or_none()
    if not html:
        raise FileNotFoundError("HTML file not found for the given document ID.")
    with open(html.file_path, 'rb') as f:
        html_content = f.read()

    html_file_obj = BytesIO(html_content)
    docx_content, _ = convert_file(html_file_obj, html.file_name, 'html', 'docx')
    if not docx_content:
        raise FileNotFoundError("DOCX conversion failed.")

    with open(html.file_path.replace('.html', '.docx'), 'wb') as f:
        f.write(docx_content)


# -------------------------------------------------------
# Delete a document
# -------------------------------------------------------
def delete_document(session, doc_id):
    doc = session.query(Document).filter_by(id=doc_id, user_id=current_user.id).one_or_none()
    html = session.query(HtmlFile).filter_by(doc_id=doc_id, user_id=current_user.id).one_or_none()

    if not doc:
        return False

    doc_folder = os.path.dirname(doc.file_path)
    shutil.rmtree(doc_folder, ignore_errors=True)

    if html:
        session.delete(html)
    session.delete(doc)
    session.commit()
    return True


# -------------------------------------------------------
# Get list of other users
# -------------------------------------------------------
def get_other_users(session):
    return session.query(User.id, User.username).filter(User.id != current_user.id).all()


# -------------------------------------------------------
# Share a document with another user
# -------------------------------------------------------
def share_document(session, document_id, invited_user_id):
    doc = session.query(Document).filter_by(id=document_id, user_id=current_user.id).one_or_none()
    if not doc:
        return {"error": "Document not found"}, 404

    invited_user = session.query(User).filter_by(id=invited_user_id).one_or_none()
    if not invited_user:
        return {"error": "Invited user not found"}, 404

    existing_share = session.query(SharedDocument).filter_by(
        document_id=document_id,
        invited_user_id=invited_user_id
    ).one_or_none()
    if existing_share:
        return {"error": "Document already shared with this user"}, 400

    new_shared_doc = SharedDocument(
        invited_user_id=invited_user_id,
        document_id=document_id,
        invited_by=current_user.id
    )

    session.add(new_shared_doc)
    session.commit()
    return {"message": "Document shared successfully"}


# -------------------------------------------------------
# Get documents shared *with* the current user
# -------------------------------------------------------
def get_shared_documents_with_user(session):
    shared_docs = (
        session.query(Document)
        .join(SharedDocument, Document.id == SharedDocument.document_id)
        .filter(SharedDocument.invited_user_id == current_user.id)
        .all()
    )
    print("SHARED DOCS:", shared_docs)
    docs = []
    for doc in shared_docs:
        print("Invited by:", session.query(User.username)
                .join(SharedDocument, User.id == SharedDocument.invited_by)
                .filter(SharedDocument.document_id == doc.id)
                .all())
        tempdoc = {
            "id": str(doc.id),
            "name": doc.file_name,
            "created_at": doc.created_at.isoformat(),
            "invited_by_user_name": (
                session.query(User.username)
                .join(SharedDocument, User.id == SharedDocument.invited_by)
                .filter(and_(SharedDocument.document_id == doc.id,
                            SharedDocument.invited_user_id == current_user.id))
                .scalar()
            )
        }
        docs.append(tempdoc)
    return docs


# -------------------------------------------------------
# Get documents shared *by* the current user
# -------------------------------------------------------
def get_shared_documents_by_user(session):
    shared_docs = (session.query(Document)
        .join(SharedDocument, Document.id == SharedDocument.document_id).filter(SharedDocument.invited_by == current_user.id)
        .all()
    )
    resdoc = []
    for doc in shared_docs:
        doc_info = {
            "doc": doc.to_dict(),
            "shared_with": [
                { "username": username[0], "id": username[1] } for username in
                session.query(User.username, User.id).join(SharedDocument, User.id == SharedDocument.invited_user_id).filter(SharedDocument.document_id == doc.id).all()
            ]
        }
        resdoc.append(doc_info)
    print("RESDOC:", resdoc)
    return resdoc

def is_owner(session, doc_id):
    doc = session.query(Document).filter_by(id=doc_id).first()
    if not doc:
        return jsonify({'error': 'Document not found'}), 404

    if doc.user_id == current_user.id:
        return jsonify({'is_owner': True}), 200
    else:
        return jsonify({'is_owner': False}), 200

def unshare_document(session, document_id, invited_user_id):
    shared_doc = session.query(SharedDocument).filter_by(
        document_id=document_id,
        invited_user_id=invited_user_id,
        invited_by=current_user.id
    ).first()

    if not shared_doc:
        return {"error": "Shared document entry not found"}, 404

    session.delete(shared_doc)
    session.commit()
    return {"message": "Document unshared successfully"}