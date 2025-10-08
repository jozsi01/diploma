import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


# ============================================
# Document Model
# ============================================
class Document(Base):
    __tablename__ = 'documents'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_name = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships (1:1)
    html_file = relationship("HtmlFile", back_populates="document", uselist=False, cascade="all, delete-orphan")
    pdf_file = relationship("PdfFile", back_populates="document", uselist=False, cascade="all, delete-orphan")

    user = relationship("User", back_populates="documents")
    def __repr__(self):
        return f"<Document(id={self.id}, file_name='{self.file_name}')>"
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.file_name,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# ============================================
# HTML File Model (1:1 with Document)
# ============================================
class HtmlFile(Base):
    __tablename__ = 'html_files'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doc_id = Column(UUID(as_uuid=True), ForeignKey('documents.id', ondelete='CASCADE'), nullable=False, unique=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationship back to Document
    document = relationship("Document", back_populates="html_file")

    def __repr__(self):
        return f"<HtmlFile(id={self.id}, file_name='{self.file_name}', doc_id={self.doc_id})>"


# ============================================
# PDF File Model (1:1 with Document)
# ============================================
class PdfFile(Base):
    __tablename__ = 'pdf_files'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doc_id = Column(UUID(as_uuid=True), ForeignKey('documents.id', ondelete='CASCADE'), nullable=False, unique=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationship back to Document
    document = relationship("Document", back_populates="pdf_file")

    def __repr__(self):
        return f"<PdfFile(id={self.id}, file_name='{self.file_name}', doc_id={self.doc_id})>"

class User(Base):
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(150), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"