"""Conversation database model."""
import uuid
from datetime import datetime
from typing import List
from sqlalchemy import Index
from sqlalchemy.dialects.postgresql import UUID
from app.extensions import db


class Conversation(db.Model):
    """Conversation model representing a chat thread between student and tutor."""

    __tablename__ = 'conversations'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = db.Column(db.Text, nullable=True)  # Auto-generated from first message
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relationship to messages (one-to-many)
    messages = db.relationship(
        'Message',
        backref='conversation',
        lazy='dynamic',
        cascade='all, delete-orphan',
        order_by='Message.created_at'
    )

    # Index for recent thread listing
    __table_args__ = (
        Index('ix_conversations_created_at_desc', created_at.desc()),
    )

    def __repr__(self) -> str:
        """String representation of Conversation."""
        return f"<Conversation {self.id}: '{self.title or 'Untitled'}'>"

    def to_dict(self) -> dict:
        """Convert conversation to dictionary."""
        return {
            'id': str(self.id),
            'title': self.title,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
