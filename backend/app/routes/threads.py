"""Thread/conversation API endpoints."""
import logging
from flask import Blueprint, jsonify, request
from sqlalchemy import desc
from sqlalchemy.orm import joinedload
from app.extensions import db
from app.models import Conversation, Message
from app.utils.errors import AppError, ErrorCodes

logger = logging.getLogger(__name__)

threads_bp = Blueprint('threads', __name__, url_prefix='/api/threads')


@threads_bp.route('', methods=['GET'])
def list_threads():
    """List recent conversation threads.

    Query Parameters:
        limit: int (default 20, max 100) - number of threads to return

    Returns:
        JSON array of threads with metadata and last message preview
    """
    try:
        # Parse limit parameter
        limit = request.args.get('limit', 20, type=int)
        limit = min(limit, 100)  # Cap at 100

        # Query conversations ordered by most recent
        conversations = db.session.query(Conversation)\
            .order_by(desc(Conversation.updated_at))\
            .limit(limit)\
            .all()

        # Build response with last message preview
        threads = []
        for conv in conversations:
            # Get last message
            last_message = db.session.query(Message)\
                .filter_by(conversation_id=conv.id)\
                .order_by(desc(Message.created_at))\
                .first()

            thread_data = {
                'id': str(conv.id),
                'title': conv.title or 'Untitled Thread',
                'created_at': conv.created_at.isoformat() if conv.created_at else None,
                'updated_at': conv.updated_at.isoformat() if conv.updated_at else None,
                'last_message_preview': None
            }

            if last_message:
                # Truncate at 50 characters
                preview = last_message.content[:50]
                if len(last_message.content) > 50:
                    preview += '...'
                thread_data['last_message_preview'] = preview

            threads.append(thread_data)

        logger.info(f"Listed {len(threads)} threads")
        return jsonify(threads), 200

    except Exception as e:
        logger.error(f"Error listing threads: {e}", exc_info=True)
        raise AppError(
            'Failed to list threads',
            ErrorCodes.INTERNAL_ERROR,
            500
        )


@threads_bp.route('/<thread_id>', methods=['GET'])
def get_thread(thread_id):
    """Load a conversation thread with all messages.

    Args:
        thread_id: UUID of the conversation

    Returns:
        JSON object with conversation and messages
    """
    try:
        # Load conversation (messages loaded via dynamic relationship)
        conversation = db.session.query(Conversation)\
            .filter_by(id=thread_id)\
            .first()

        if not conversation:
            raise AppError(
                f'Conversation {thread_id} not found',
                ErrorCodes.NOT_FOUND,
                404
            )

        # Build response - messages already ordered by created_at in relationship
        messages = [msg.to_dict() for msg in conversation.messages.all()]

        response = {
            'id': str(conversation.id),
            'title': conversation.title or 'Untitled Thread',
            'created_at': conversation.created_at.isoformat() if conversation.created_at else None,
            'updated_at': conversation.updated_at.isoformat() if conversation.updated_at else None,
            'messages': messages
        }

        logger.info(f"Loaded thread {thread_id} with {len(messages)} messages")
        return jsonify(response), 200

    except AppError:
        raise
    except Exception as e:
        logger.error(f"Error loading thread {thread_id}: {e}", exc_info=True)
        raise AppError(
            'Failed to load thread',
            ErrorCodes.INTERNAL_ERROR,
            500
        )


@threads_bp.route('/<thread_id>', methods=['DELETE'])
def delete_thread(thread_id):
    """Delete a conversation thread.

    Args:
        thread_id: UUID of the conversation to delete

    Returns:
        JSON confirmation message
    """
    try:
        conversation = db.session.query(Conversation).filter_by(id=thread_id).first()

        if not conversation:
            raise AppError(
                f'Conversation {thread_id} not found',
                ErrorCodes.NOT_FOUND,
                404
            )

        # Delete conversation (cascade will delete messages)
        db.session.delete(conversation)
        db.session.commit()

        logger.info(f"Deleted thread {thread_id}")
        return jsonify({'message': 'Thread deleted successfully'}), 200

    except AppError:
        raise
    except Exception as e:
        logger.error(f"Error deleting thread {thread_id}: {e}", exc_info=True)
        db.session.rollback()
        raise AppError(
            'Failed to delete thread',
            ErrorCodes.INTERNAL_ERROR,
            500
        )
