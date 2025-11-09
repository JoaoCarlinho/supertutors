"""Message database model."""
import uuid
import enum
from datetime import datetime
from sqlalchemy import Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.extensions import db


class MessageRole(enum.Enum):
    """Enum for message roles."""
    STUDENT = 'student'
    TUTOR = 'tutor'
    SYSTEM = 'system'


class Message(db.Model):
    """Message model representing a single message in a conversation."""

    __tablename__ = 'messages'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey('conversations.id', ondelete='CASCADE'),
        nullable=False
    )
    role = db.Column(db.Enum(MessageRole), nullable=False)
    content = db.Column(db.Text, nullable=False)
    message_metadata = db.Column(JSONB, nullable=True, default=dict)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Index for efficient message retrieval within a conversation
    __table_args__ = (
        Index('ix_messages_conversation_created', conversation_id, created_at.desc()),
    )

    def __repr__(self) -> str:
        """String representation of Message."""
        preview = self.content[:50] + '...' if len(self.content) > 50 else self.content
        return f"<Message {self.id}: {self.role.value} - '{preview}'>"

    def to_dict(self) -> dict:
        """Convert message to dictionary."""
        return {
            'id': str(self.id),
            'conversation_id': str(self.conversation_id),
            'role': self.role.value,
            'content': self.content,
            'metadata': self.message_metadata,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None
        }
