import os
import uuid
import subprocess
import logging
import tempfile
from io import BytesIO
import sys
from flask import jsonify
from flask import request
from flask_jwt_extended import current_user
from database.models import Document, HtmlFile, User, SharedDocument
from sqlalchemy import and_
from azure.core.exceptions import ResourceExistsError
from azure.storage.blob import BlobServiceClient, ContentSettings
from html_management import format_image_srcs
from werkzeug.utils import secure_filename

# Logging konfiguráció
# A szintet INFO-ra állítjuk, hogy a Docker logokban minden fontos esemény látsszon
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    stream=sys.stdout,
    force=True
)
logger = logging.getLogger(__name__)
BLOB_CONTAINER_NAME = "documents"
_blob_service_client = None
_blob_container_client = None


def get_blob_container_client():
    global _blob_service_client, _blob_container_client

    if _blob_container_client is not None:
        return _blob_container_client

    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    if not connection_string:
        raise RuntimeError("AZURE_STORAGE_CONNECTION_STRING is not set")

    if _blob_service_client is None:
        _blob_service_client = BlobServiceClient.from_connection_string(connection_string)

    container_client = _blob_service_client.get_container_client(BLOB_CONTAINER_NAME)
    try:
        container_client.create_container()
    except ResourceExistsError:
        pass

    _blob_container_client = container_client
    return _blob_container_client


def build_blob_name(doc_id, filename):
    user_id_short = str(current_user.id)[:4] if current_user else "anon"
    safe_filename = secure_filename(filename) or filename
    return os.path.join(f"user_{user_id_short}", str(doc_id), safe_filename).replace("\\", "/")


def build_blob_route_base(blob_name):
    blob_prefix = os.path.dirname(blob_name).replace("\\", "/")
    try:
        return request.host_url.rstrip("/") + f"/api/documents/{blob_prefix}"
    except RuntimeError:
        return f"/api/documents/{blob_prefix}"


def infer_content_type(filename):
    lower_name = filename.lower()
    if lower_name.endswith(".html") or lower_name.endswith(".htm"):
        return "text/html; charset=utf-8"
    if lower_name.endswith(".docx"):
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    if lower_name.endswith(".pdf"):
        return "application/pdf"
    if lower_name.endswith(".png"):
        return "image/png"
    if lower_name.endswith(".jpg") or lower_name.endswith(".jpeg"):
        return "image/jpeg"
    if lower_name.endswith(".gif"):
        return "image/gif"
    if lower_name.endswith(".svg"):
        return "image/svg+xml"
    if lower_name.endswith(".css"):
        return "text/css; charset=utf-8"
    if lower_name.endswith(".js"):
        return "application/javascript; charset=utf-8"
    return "application/octet-stream"


def upload_blob(blob_name, content, content_type=None):
    if isinstance(content, str):
        content = content.encode("utf-8")

    blob_client = get_blob_container_client().get_blob_client(blob_name)
    blob_client.upload_blob(
        content,
        overwrite=True,
        content_settings=ContentSettings(content_type=content_type or infer_content_type(blob_name)),
    )
    logger.info("Uploaded blob: %s", blob_name)
    return blob_name


def download_blob_bytes(blob_name):
    blob_client = get_blob_container_client().get_blob_client(blob_name)
    return blob_client.download_blob().readall()


def download_blob_text(blob_name):
    return download_blob_bytes(blob_name).decode("utf-8")


def download_blob_prefix_to_directory(blob_prefix, target_directory):
    container_client = get_blob_container_client()
    prefix = blob_prefix.rstrip("/") + "/"

    for blob in container_client.list_blobs(name_starts_with=prefix):
        relative_path = blob.name[len(prefix):]
        local_path = os.path.join(target_directory, relative_path.replace("/", os.sep))
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, "wb") as file_handle:
            file_handle.write(download_blob_bytes(blob.name))


def upload_directory_to_blob(source_directory, blob_prefix):
    for root, _, files in os.walk(source_directory):
        for file_name in files:
            if file_name in {"temp.docx", "temp.odt", "temp.html", "temp.pdf"}:
                continue

            local_path = os.path.join(root, file_name)
            relative_path = os.path.relpath(local_path, source_directory).replace("\\", "/")
            blob_name = f"{blob_prefix.rstrip('/')}/{relative_path}"
            with open(local_path, "rb") as file_handle:
                upload_blob(blob_name, file_handle.read())

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
# Save document file to Blob Storage
# -------------------------------------------------------
def save_document(file, filename, doc_id):
    blob_name = build_blob_name(doc_id, filename)
    logger.info("Saving file to blob: %s", blob_name)
    upload_blob(blob_name, file)
    return blob_name

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

        with tempfile.TemporaryDirectory() as temp_dir:
            file_for_conv = BytesIO(content)
            html_file, html_filename = convert_file(file_for_conv, filename, 'docx', 'html', temp_dir)

            if not html_file:
                logger.error(f"Initial HTML conversion failed for {filename}")
                return None

            base_url = build_blob_route_base(path)
            logger.debug(f"Formatting HTML images with base_url: {base_url}")
            html_file = format_image_srcs(html_file, base_url=base_url)
            path_html = save_document(html_file, html_filename, doc_id)

            upload_directory_to_blob(temp_dir, os.path.dirname(path))

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
        return download_blob_text(html_file_path[0])
    except Exception as e:
        logger.error(f"Could not read HTML file from blob storage: {html_file_path[0]}. Error: {str(e)}")
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
        upload_blob(html.file_path, html_content, content_type="text/html; charset=utf-8")
        logger.info(f"HTML content successfully updated in blob storage: {html.file_path}")
        return jsonify({'message': 'Document updated successfully'}), 200
    except Exception as e:
        logger.error(f"Blob write error during HTML save: {str(e)}")
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

    prefix = os.path.dirname(html.file_path)

    with tempfile.TemporaryDirectory() as temp_dir:
        download_blob_prefix_to_directory(prefix, temp_dir)
        html_content = download_blob_bytes(html.file_path)
        html_file_obj = BytesIO(html_content)
        docx_content, _ = convert_file(html_file_obj, html.file_name, 'html', 'docx', temp_dir)

        if not docx_content:
            logger.error("HTML to DOCX conversion failed during sync.")
            raise FileNotFoundError("DOCX conversion failed.")

        target_path = html.file_path.replace('.html', '.docx')
        upload_blob(target_path, docx_content)
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

    prefix = os.path.dirname(html.file_path)

    with tempfile.TemporaryDirectory() as temp_dir:
        download_blob_prefix_to_directory(prefix, temp_dir)
        html_content = download_blob_bytes(html.file_path)
        html_file_obj = BytesIO(html_content)
        pdf_content, _ = convert_file(html_file_obj, html.file_name, 'html', 'pdf', temp_dir)

        if not pdf_content:
            logger.error("HTML to PDF conversion failed.")
            raise FileNotFoundError("PDF conversion failed.")

        target_path = html.file_path.replace('.html', '.pdf')
        upload_blob(target_path, pdf_content)
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
        doc_prefix = os.path.dirname(doc.file_path)
        container_client = get_blob_container_client()
        for blob in container_client.list_blobs(name_starts_with=f"{doc_prefix.rstrip('/')}/"):
            logger.info(f"Deleting blob: {blob.name}")
            container_client.delete_blob(blob.name)

        if html:
            session.delete(html)
        session.delete(doc)
        session.commit()
        logger.info(f"Document {doc_id} successfully deleted from blob storage and DB.")
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