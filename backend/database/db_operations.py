import os
import uuid
import shutil
import subprocess
import logging
from io import BytesIO

from flask import jsonify
from flask_jwt_extended import current_user
from database.models import Document, HtmlFile, User, SharedDocument
from sqlalchemy import and_
from html_management import format_image_srcs

# Logging konfiguráció
# A szintet INFO-ra állítjuk, hogy a Docker logokban minden fontos esemény látsszon
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

# -------------------------------------------------------
# Fetch all documents for the current user
# -------------------------------------------------------
def fetch_all_documents_for_user(session):
    user_id = current_user.id if current_user else "Unknown"
    logger.info(f"Fetching all documents for user_id: {user_id}")
    
    try:
        documents = session.query(Document).filter_by(user_id=current_user.id).all()
        logger.debug(f"Found {len(documents)} documents for user {user_id}")
        return [doc.to_dict() for doc in documents]
    except Exception as e:
        logger.error(f"Error fetching documents for user {user_id}: {str(e)}")
        return []

# -------------------------------------------------------
# Convert a file between formats (e.g., DOCX → HTML)
# -------------------------------------------------------
def convert_file(file, filename, input_format, output_format, cwd=os.getcwd()):
    if hasattr(file, 'read'):
        file.seek(0)
        content = file.read()
    else:
        content = file

    clean_filename = filename.rsplit('.', 1)[0]
    
    input_path = os.path.join(cwd, f"temp.{input_format}")
    odt_path = os.path.join(cwd, "temp.odt")
    output_path = os.path.join(cwd, f"temp.{output_format}")

    logger.info(f"Conversion started: {input_format} -> {output_format} | File: {filename}")
    
    with open(input_path, "wb") as f:
        f.write(content)

    try:
        # 1. fázis: Konvertálás köztes ODT formátumba
        logger.debug(f"Phase 1: {input_format} -> ODT")
        first_conv = subprocess.run([
            'soffice', '--headless', '--norestore', '--nofirststartwizard',
            '-env:UserInstallation=file:///tmp/libreoffice-profile',
            '--convert-to', 'odt', f'temp.{input_format}'
        ], check=True, text=True, capture_output=True, cwd=cwd)

        # 2. fázis: ODT -> Cél formátum
        logger.debug(f"Phase 2: ODT -> {output_format}")
        second_conv = subprocess.run([
            'soffice', '--headless', '--norestore', '--nofirststartwizard',
            '-env:UserInstallation=file:///tmp/libreoffice-profile',
            '--convert-to', output_format, 'temp.odt'
        ], check=True, text=True, capture_output=True, cwd=cwd)

        if first_conv.stderr or second_conv.stderr:
            logger.warning(f"LibreOffice stderr detected: {first_conv.stderr} {second_conv.stderr}")

        with open(output_path, 'rb') as f:
            converted_content = f.read()
            logger.info(f"Conversion successful: {output_path}")
            return converted_content, f'{clean_filename}.{output_format}'

    except subprocess.CalledProcessError as e:
        logger.error(f"LibreOffice conversion failed! Stderr: {e.stderr}")
        return None, None
    except Exception as e:
        logger.error(f"Unexpected error during conversion: {str(e)}")
        return None, None

    finally:
        if hasattr(file, 'seek'):
            file.seek(0)

        for temp_path in [input_path, odt_path, output_path]:
            if os.path.exists(temp_path):
                logger.debug(f"Cleaning up temp file: {temp_path}")
                os.remove(temp_path)

# -------------------------------------------------------
# Save document file to disk
# -------------------------------------------------------
def save_document(file, filename, doc_id):
    user_id_short = str(current_user.id)[:4] if current_user else "anon"
    user_folder = os.path.join('documents', f'user_{user_id_short}', str(doc_id))
    os.makedirs(user_folder, exist_ok=True)

    file_path = os.path.join(user_folder, filename)
    logger.info(f"Saving file to: {file_path}")
    
    with open(file_path, 'wb') as f:
        f.write(file)
    return file_path

# -------------------------------------------------------
# Create a new document and HTML version for user
# -------------------------------------------------------
def create_document_for_user(session, file, filename):
    doc_id = uuid.uuid4()
    html_id = uuid.uuid4()
    logger.info(f"Starting document creation: {filename} (ID: {doc_id})")

    try:
        content = file.read()
        path = save_document(content, filename, doc_id)
        
        # Konvertáláshoz új BytesIO objektum kell a mentett tartalomból
        file_for_conv = BytesIO(content)
        html_file, html_filename = convert_file(file_for_conv, filename, 'docx', 'html', os.path.dirname(path))
        
        if not html_file:
            logger.error(f"Initial HTML conversion failed for {filename}")
            return None

        base_url = "/api/" + os.path.dirname(path)
        base_url = base_url.replace('\\', '/')
        
        logger.debug(f"Formatting HTML images with base_url: {base_url}")
        html_file = format_image_srcs(html_file, base_url=base_url)
        path_html = save_document(html_file, html_filename, doc_id)

        new_document = Document(
            id=doc_id, user_id=current_user.id, 
            file_name=filename, file_path=path
        )
        new_html = HtmlFile(
            id=html_id, doc_id=doc_id, 
            file_name=html_filename, file_path=path_html, 
            user_id=current_user.id
        )

        session.add(new_document)
        session.add(new_html)
        session.commit()
        session.refresh(new_document)
        
        logger.info(f"Document and HTML metadata committed to DB for user {current_user.id}")
        return new_document
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to create document for user: {str(e)}")
        return None

# -------------------------------------------------------
# Get HTML content for editing
# -------------------------------------------------------
def get_html_for_edit(session, doc_id):
    logger.info(f"Fetching HTML content for edit. DocID: {doc_id}")
    html_file_path = session.query(HtmlFile.file_path).filter_by(doc_id=doc_id).one_or_none()
    
    if not html_file_path:
        logger.warning(f"No HTML file path found in DB for DocID: {doc_id}")
        return None

    try:
        with open(html_file_path[0], 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Could not read HTML file from disk: {html_file_path[0]}. Error: {str(e)}")
        return None

# -------------------------------------------------------
# Save edited HTML content
# -------------------------------------------------------
def save_html_content(session, doc_id, html_content):
    html = session.query(HtmlFile).filter_by(doc_id=doc_id).one_or_none()
    
    if not html:
        logger.error(f"Save failed: HTML metadata not found for DocID {doc_id}")
        return jsonify({'error': 'HTML file not found'}), 404

    logger.info(f"Save HTML request by User: {current_user.id} | Owner ID: {html.user_id}")

    if html.user_id != current_user.id:
        logger.warning(f"Unauthorized access attempt! User {current_user.id} tried to edit Doc {doc_id}")
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        with open(html.file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"HTML content successfully updated on disk: {html.file_path}")
        return jsonify({'message': 'Document updated successfully'}), 200
    except Exception as e:
        logger.error(f"Disk write error during HTML save: {str(e)}")
        return jsonify({'error': 'Internal Server Error during save'}), 500

# -------------------------------------------------------
# Retrieve a DOCX document
# -------------------------------------------------------
def get_docx(session, doc_id):
    logger.info(f"Retrieving DOCX metadata for DocID: {doc_id}")
    return session.query(Document).filter_by(id=doc_id, user_id=current_user.id).one_or_none()

# -------------------------------------------------------
# Update DOCX from latest HTML
# -------------------------------------------------------
def update_docx(session, doc_id):
    logger.info(f"Syncing DOCX from HTML for DocID: {doc_id}")
    html = session.query(HtmlFile).filter_by(doc_id=doc_id, user_id=current_user.id).one_or_none()
    
    if not html:
        logger.error(f"Update DOCX failed: HTML not found for DocID {doc_id}")
        raise FileNotFoundError("HTML file not found for the given document ID.")

    with open(html.file_path, 'rb') as f:
        html_content = f.read()

    html_file_obj = BytesIO(html_content)
    docx_content, _ = convert_file(html_file_obj, html.file_name, 'html', 'docx', os.path.dirname(html.file_path))
    
    if not docx_content:
        logger.error("HTML to DOCX conversion failed during sync.")
        raise FileNotFoundError("DOCX conversion failed.")

    target_path = html.file_path.replace('.html', '.docx')
    with open(target_path, 'wb') as f:
        f.write(docx_content)
    logger.info(f"DOCX updated successfully at: {target_path}")

# -------------------------------------------------------
# Update PDF from HTML
# -------------------------------------------------------
def update_pdf(session, doc_id):
    logger.info(f"Generating PDF for DocID: {doc_id}")
    html = session.query(HtmlFile).filter_by(doc_id=doc_id, user_id=current_user.id).one_or_none()
    
    if not html:
        logger.error(f"PDF generation failed: HTML not found for DocID {doc_id}")
        raise FileNotFoundError("HTML file not found for the given document ID.")

    with open(html.file_path, 'rb') as f:
        html_content = f.read()

    html_file_obj = BytesIO(html_content)
    pdf_content, _ = convert_file(html_file_obj, html.file_name, 'html', 'pdf', os.path.dirname(html.file_path))
    
    if not pdf_content:
        logger.error("HTML to PDF conversion failed.")
        raise FileNotFoundError("PDF conversion failed.")

    target_path = html.file_path.replace('.html', '.pdf')
    with open(target_path, 'wb') as f:
        f.write(pdf_content)
    logger.info(f"PDF generated successfully at: {target_path}")

# -------------------------------------------------------
# Delete a document
# -------------------------------------------------------
def delete_document(session, doc_id):
    logger.info(f"Request to delete DocID: {doc_id} from User: {current_user.id}")
    doc = session.query(Document).filter_by(id=doc_id, user_id=current_user.id).one_or_none()
    html = session.query(HtmlFile).filter_by(doc_id=doc_id, user_id=current_user.id).one_or_none()

    if not doc:
        logger.warning(f"Delete failed: Document {doc_id} not found or user is not owner.")
        return False

    try:
        doc_folder = os.path.dirname(doc.file_path)
        if os.path.exists(doc_folder):
            logger.info(f"Deleting folder from disk: {doc_folder}")
            shutil.rmtree(doc_folder, ignore_errors=True)

        if html:
            session.delete(html)
        session.delete(doc)
        session.commit()
        logger.info(f"Document {doc_id} successfully deleted from disk and DB.")
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"Error during document deletion: {str(e)}")
        return False

# -------------------------------------------------------
# Get list of other users
# -------------------------------------------------------
def get_other_users(session):
    logger.debug(f"Fetching users list (excluding current user: {current_user.id})")
    return session.query(User.id, User.username).filter(User.id != current_user.id).all()

# -------------------------------------------------------
# Share a document with another user
# -------------------------------------------------------
def share_document(session, document_id, invited_user_id):
    logger.info(f"User {current_user.id} sharing Doc {document_id} with User {invited_user_id}")
    
    doc = session.query(Document).filter_by(id=document_id, user_id=current_user.id).one_or_none()
    if not doc:
        logger.error("Share failed: Document not found or not owned by sender.")
        return {"error": "Document not found"}, 404

    invited_user = session.query(User).filter_by(id=invited_user_id).one_or_none()
    if not invited_user:
        logger.error(f"Share failed: Target user {invited_user_id} does not exist.")
        return {"error": "Invited user not found"}, 404

    existing_share = session.query(SharedDocument).filter_by(
        document_id=document_id, invited_user_id=invited_user_id
    ).one_or_none()
    
    if existing_share:
        logger.warning("Share failed: Document already shared with this user.")
        return {"error": "Document already shared with this user"}, 400

    try:
        new_shared_doc = SharedDocument(
            invited_user_id=invited_user_id,
            document_id=document_id,
            invited_by=current_user.id
        )
        session.add(new_shared_doc)
        session.commit()
        logger.info("Document shared successfully.")
        return {"message": "Document shared successfully"}
    except Exception as e:
        session.rollback()
        logger.error(f"Database error during sharing: {str(e)}")
        return {"error": "Internal server error"}, 500

# -------------------------------------------------------
# Get documents shared *with* the current user
# -------------------------------------------------------
def get_shared_documents_with_user(session):
    logger.info(f"Fetching documents shared WITH user {current_user.id}")
    shared_docs = (
        session.query(Document)
        .join(SharedDocument, Document.id == SharedDocument.document_id)
        .filter(SharedDocument.invited_user_id == current_user.id)
        .all()
    )
    
    docs = []
    for doc in shared_docs:
        inviter_name = (
            session.query(User.username)
            .join(SharedDocument, User.id == SharedDocument.invited_by)
            .filter(and_(SharedDocument.document_id == doc.id,
                         SharedDocument.invited_user_id == current_user.id))
            .scalar()
        )
        docs.append({
            "id": str(doc.id),
            "name": doc.file_name,
            "created_at": doc.created_at.isoformat(),
            "invited_by_user_name": inviter_name
        })
    
    logger.debug(f"Found {len(docs)} documents shared with user.")
    return docs

# -------------------------------------------------------
# Get documents shared *by* the current user
# -------------------------------------------------------
def get_shared_documents_by_user(session):
    logger.info(f"Fetching documents shared BY user {current_user.id}")
    shared_docs = (
        session.query(Document)
        .join(SharedDocument, Document.id == SharedDocument.document_id)
        .filter(SharedDocument.invited_by == current_user.id)
        .all()
    )
    
    resdoc = []
    for doc in shared_docs:
        shared_with = session.query(User.username, User.id)\
            .join(SharedDocument, User.id == SharedDocument.invited_user_id)\
            .filter(SharedDocument.document_id == doc.id).all()
            
        resdoc.append({
            "doc": doc.to_dict(),
            "shared_with": [{"username": u[0], "id": u[1]} for u in shared_with]
        })
    
    logger.debug(f"Found {len(resdoc)} documents shared by user.")
    return resdoc

def is_owner(session, doc_id):
    logger.debug(f"Checking ownership for Doc {doc_id} (User {current_user.id})")
    doc = session.query(Document).filter_by(id=doc_id).first()
    if not doc:
        return jsonify({'error': 'Document not found'}), 404

    return jsonify({'is_owner': doc.user_id == current_user.id}), 200

def unshare_document(session, document_id, invited_user_id):
    logger.info(f"User {current_user.id} unsharing Doc {document_id} from User {invited_user_id}")
    shared_doc = session.query(SharedDocument).filter_by(
        document_id=document_id,
        invited_user_id=invited_user_id,
        invited_by=current_user.id
    ).first()

    if not shared_doc:
        logger.warning("Unshare failed: Shared entry not found.")
        return {"error": "Shared document entry not found"}, 404

    try:
        session.delete(shared_doc)
        session.commit()
        logger.info("Document unshared successfully.")
        return {"message": "Document unshared successfully"}
    except Exception as e:
        session.rollback()
        logger.error(f"Database error during unsharing: {str(e)}")
        return {"error": "Internal server error"}, 500