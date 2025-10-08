import subprocess
import os
import uuid
from database.database import SessionLocal
from database.models import Document, HtmlFile
from flask_jwt_extended import current_user

def fetch_all_documents_for_user():
    # Logic to fetch all documents for a specific user from the database

    session = SessionLocal()
    print("Current User in DB Operation:", current_user)
    documents = session.query(Document).filter_by(user_id=current_user.id).all()
    print(documents)
    session.close()
    return documents

def create_document_for_user(file, filename):
    session = SessionLocal()
    doc_id =  uuid.uuid4()
    html_id = uuid.uuid4()
    html_file, html_filename = convert_file(file,filename,'docx','html')
    path = save_document(file.read(),filename,doc_id)
    path_html = save_document(html_file,html_filename,doc_id)
    new_document = Document(id=doc_id, user_id=current_user.id, file_name=filename, file_path=path)
    new_html = HtmlFile(id=html_id, doc_id=doc_id, file_name=html_filename, file_path=path_html)   
    session.add(new_document)
    session.add(new_html)
    session.commit()
    session.refresh(new_document)
    session.close()
    return new_document

def get_html_for_edit(doc_id):
    session = SessionLocal()
    html_file_path = session.query(HtmlFile.file_path).filter_by(doc_id=doc_id).one_or_none()
    session.close()
    if html_file_path:
        with open(html_file_path[0], 'r', encoding='utf-8') as f:
            return f.read()

def convert_file(file,filename,input_format,output_format):
    file.seek(0)
    content = file.read()
    filename = filename.rsplit('.', 1)[0]
    with open(f"temp.{input_format}", "wb") as f:
        f.write(content)
    try:
        subprocess.run([
            'soffice',
            '--headless',
            '--convert-to', 
            'odt',
            f'temp.{input_format}',
        ],check=True,text=True)

        subprocess.run([
            'soffice',
            '--headless',
            '--convert-to',
            f'{output_format}',
            f'temp.odt',
        ],check=True,text=True)

        with open(f'temp.{output_format}', 'rb') as f:
            converted_content = f.read()
            return converted_content, f'{filename}.{output_format}'
    except subprocess.CalledProcessError as e:
        print("Error during conversion:", e)
        return None, None
    finally:
        file.seek(0)
        if os.path.exists(f'temp.{input_format}'):
            os.remove(f'temp.{input_format}')
        if os.path.exists('temp.odt'):
            os.remove('temp.odt')
        if os.path.exists(f'temp.{output_format}'):
            os.remove(f'temp.{output_format}')


def save_document(file,filename,doc_id):
    user_folder = os.path.join('documents', f'user_{str(current_user.id)[:4]}', str(doc_id))
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)

    file_path = os.path.join(user_folder, filename)
    with open(file_path, 'wb') as f:
        f.write(file)
    
    return file_path

def save_html_content(doc_id, html_content):
    session = SessionLocal()
    html_filepath = session.query(HtmlFile.file_path).filter_by(doc_id=doc_id).one_or_none()
    if not html_filepath:
        session.close()
        return False

    with open(html_filepath[0], 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    session.close()
    return True
    
