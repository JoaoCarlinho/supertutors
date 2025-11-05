"""WebSocket event handlers for Flask-SocketIO."""
import logging
import uuid
from datetime import datetime
from flask import request
from flask_socketio import emit, join_room
from app.extensions import socketio, db
from app.models import Message, MessageRole, Conversation
from app.services.socratic_guard import SocraticGuard
from app.services.context_manager import ConversationContextManager
from app.services.feedback_system import EncouragingFeedbackSystem
from app.services.celebration_service import CelebrationService

logger = logging.getLogger(__name__)

# Initialize services
socratic_guard = SocraticGuard()
context_manager = ConversationContextManager()
feedback_system = EncouragingFeedbackSystem()
celebration_service = CelebrationService()


@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    logger.info(f"Client connected: {request.sid if hasattr(request, 'sid') else 'unknown'}")
    emit('connect_response', {'status': 'connected'})


@socketio.on('conversation:join')
def handle_conversation_join(data):
    """Handle client joining a conversation room."""
    conversation_id = data.get('conversation_id')
    if conversation_id:
        join_room(conversation_id)
        logger.info(f"Client {request.sid} joined conversation {conversation_id}")
        emit('conversation:joined', {'conversation_id': conversation_id})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    logger.info(f"Client disconnected: {request.sid if hasattr(request, 'sid') else 'unknown'}")


@socketio.on('ping')
def handle_ping():
    """Handle ping from client and respond with pong."""
    logger.debug("Ping received, sending pong")
    emit('pong')


# Typing indicator tracking
typing_users = {}  # {sid: {conversation_id, last_typing_time}}


@socketio.on('typing:start')
def handle_typing_start(data):
    """Handle typing start event."""
    conversation_id = data.get('conversation_id')
    if not conversation_id:
        logger.warning("typing:start received without conversation_id")
        return

    typing_users[request.sid] = {
        'conversation_id': conversation_id,
        'last_typing_time': datetime.utcnow()
    }
    logger.debug(f"User {request.sid} started typing in conversation {conversation_id}")


@socketio.on('typing:stop')
def handle_typing_stop(data):
    """Handle typing stop event."""
    if request.sid in typing_users:
        del typing_users[request.sid]
    logger.debug(f"User {request.sid} stopped typing")


@socketio.on('message:send')
def handle_message_send(data):
    """Handle message send from client.

    Expected data:
        - conversation_id: UUID of conversation
        - content: message content text
        - message_id: client-generated UUID for deduplication
    """
    try:
        conversation_id = data.get('conversation_id')
        content = data.get('content')
        client_message_id = data.get('message_id')

        # Validation
        if not all([conversation_id, content, client_message_id]):
            logger.error(f"Invalid message:send data: {data}")
            emit('message:error', {
                'error': 'Missing required fields',
                'message_id': client_message_id
            })
            return

        # Convert conversation_id to UUID if string
        try:
            conv_uuid = uuid.UUID(conversation_id) if isinstance(conversation_id, str) else conversation_id
            msg_uuid = uuid.UUID(client_message_id) if isinstance(client_message_id, str) else client_message_id
        except ValueError as e:
            logger.error(f"Invalid UUID format: {e}")
            emit('message:error', {
                'error': 'Invalid UUID format',
                'message_id': client_message_id
            })
            return

        # Check for duplicate message_id
        existing_message = db.session.query(Message).filter_by(id=msg_uuid).first()
        if existing_message:
            logger.info(f"Duplicate message {msg_uuid} ignored")
            # Send ACK anyway so client doesn't retry
            emit('message:ack', {
                'message_id': str(msg_uuid),
                'status': 'received'
            })
            return

        # Get or create conversation
        conversation = db.session.get(Conversation, conv_uuid)
        is_new_conversation = conversation is None

        if not conversation:
            # Create new conversation
            conversation = Conversation(
                id=conv_uuid,
                title=None  # Will be set from first message below
            )
            db.session.add(conversation)
            db.session.flush()  # Get the ID
            logger.info(f"Created new conversation {conv_uuid}")

        # Save student message
        student_message = Message(
            id=msg_uuid,
            conversation_id=conv_uuid,
            role=MessageRole.STUDENT,
            content=content,
            message_metadata={}
        )
        db.session.add(student_message)

        # Auto-generate title from first student message
        if is_new_conversation and conversation.title is None:
            # Truncate at 50 characters
            title = content[:50].strip()
            if len(content) > 50:
                title += '...'
            conversation.title = title if title else 'Untitled Thread'
            logger.info(f"Set conversation title: {conversation.title}")

        db.session.commit()

        logger.info(f"Saved student message {msg_uuid} in conversation {conv_uuid}")

        # Send ACK to client
        emit('message:ack', {
            'message_id': str(msg_uuid),
            'status': 'received'
        })

        # Broadcast student message to all clients in conversation
        emit('message:receive', student_message.to_dict())

        # Build conversation context
        context_summary = context_manager.build_context_summary(conv_uuid, content)

        # Generate Socratic response with validation
        result = socratic_guard.generate_validated_response(
            student_message=content,
            conversation_context=context_summary.get('recent_history')
        )

        # Add encouraging feedback
        tutor_content = feedback_system.wrap_response_with_encouragement(
            result['response'],
            context_summary,
            prepend=True
        )

        # Save tutor response
        tutor_message = Message(
            conversation_id=conv_uuid,
            role=MessageRole.TUTOR,
            content=tutor_content,
            message_metadata={
                'validation_passed': result['validation_passed'],
                'attempts': result['attempts'],
                'confidence': result['confidence'],
                'socratic_guard_enabled': True
            }
        )
        db.session.add(tutor_message)
        db.session.commit()

        logger.info(
            f"Generated tutor response {tutor_message.id} "
            f"(validated: {result['validation_passed']}, attempts: {result['attempts']})"
        )

        # Send tutor response
        emit('message:receive', tutor_message.to_dict())

    except Exception as e:
        logger.error(f"Error handling message:send: {e}", exc_info=True)
        db.session.rollback()
        emit('message:error', {
            'error': 'Internal server error',
            'message_id': data.get('message_id')
        })


@socketio.on('answer:validate')
def handle_answer_validation(data):
    """Handle answer validation and streak tracking.

    Expected data:
        - conversation_id: UUID of conversation
        - student_answer: Student's answer
        - expected_answer: Expected answer (optional)
        - is_correct: Whether answer was correct
        - current_streak: Current streak count (optional)
    """
    try:
        conversation_id = data.get('conversation_id')
        is_correct = data.get('is_correct', False)
        current_streak = data.get('current_streak', 0)

        if not conversation_id:
            logger.error("answer:validate received without conversation_id")
            emit('answer:validation_error', {'error': 'Missing conversation_id'})
            return

        # Update streak and check for celebration
        result = celebration_service.update_streak(
            conversation_id=str(conversation_id),
            is_correct=is_correct,
            current_streak=current_streak
        )

        logger.info(
            f"Streak updated for {conversation_id}: "
            f"new_streak={result['new_streak']}, "
            f"celebration={result['celebration_triggered']}"
        )

        # Send validation result back to client
        emit('answer:validated', {
            'conversation_id': conversation_id,
            'is_correct': is_correct,
            'new_streak': result['new_streak'],
            'celebration_triggered': result['celebration_triggered']
        })

    except Exception as e:
        logger.error(f"Error handling answer:validate: {e}", exc_info=True)
        emit('answer:validation_error', {
            'error': 'Failed to validate answer',
            'conversation_id': data.get('conversation_id')
        })
