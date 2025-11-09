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
from app.services.math_detector import MathDetector
from app.services.sympy_service import SymPyService
from app.services.answer_validator import AnswerValidator
from app.services.answer_checker import AnswerChecker
import time

logger = logging.getLogger(__name__)

# Initialize services
# Using OpenAI gpt-4o-mini for better instruction following and mathematical reasoning
socratic_guard = SocraticGuard(model_name="gpt-4o-mini", use_openai=True)
context_manager = ConversationContextManager()
feedback_system = EncouragingFeedbackSystem()
celebration_service = CelebrationService()
math_detector = MathDetector(min_confidence=0.6)
sympy_service = SymPyService()
answer_validator = AnswerValidator()
answer_checker = AnswerChecker()


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
        context_summary = context_manager.build_context_summary(
            conv_uuid, content
        )
        logger.info(f"[SOCKET] Context summary: message_count={context_summary.get('message_count')}, history_length={len(context_summary.get('recent_history', ''))}")

        # Detect and process mathematical expressions
        math_context = None
        math_metadata = {
            'math_detected': False,
            'expressions': [],
            'sympy_operations_used': [],
            'computation_time_ms': 0
        }

        start_time = time.time()

        try:
            # Detect math in student message
            detection_result = math_detector.detect(content)

            if detection_result['has_math']:
                logger.info(
                    f"Math detected: {len(detection_result['expressions'])} "
                    f"expressions, confidence={detection_result['confidence']}"
                )

                math_context = {
                    'detected': True,
                    'confidence': detection_result['confidence'],
                    'overall_type': detection_result['overall_type'],
                    'expressions': []
                }

                # Extract expressions for SymPy processing
                expr_strings = math_detector.extract_expressions_for_sympy(
                    detection_result
                )

                # Process each expression with SymPy
                for expr_str in expr_strings[:3]:  # Limit to 3 expressions
                    expr_result = {
                        'original': expr_str,
                        'parsed': None,
                        'simplified': None,
                        'type': None,
                        'solutions': [],
                        'steps': []
                    }

                    try:
                        # Parse expression
                        parse_result = sympy_service.parse_expression(expr_str)
                        if parse_result['success']:
                            expr_result['parsed'] = str(parse_result['result'])
                            math_metadata['sympy_operations_used'].append(
                                'parse'
                            )

                            # Simplify expression
                            simplify_result = sympy_service.simplify_expression(
                                expr_str
                            )
                            if simplify_result['success']:
                                expr_result['simplified'] = (
                                    simplify_result['result']
                                )
                                math_metadata['sympy_operations_used'].append(
                                    'simplify'
                                )

                            # If it's an equation, try to solve it
                            if '=' in expr_str:
                                expr_result['type'] = 'equation'
                                solve_result = sympy_service.solve_equation(
                                    expr_str
                                )
                                if (solve_result['success'] and
                                        solve_result['result']['solvable']):
                                    expr_result['solutions'] = (
                                        solve_result['result']['solutions']
                                    )
                                    math_metadata[
                                        'sympy_operations_used'
                                    ].append('solve')

                                    # Generate solution steps
                                    steps_result = (
                                        answer_validator.generate_solution_steps(
                                            expr_str
                                        )
                                    )
                                    if steps_result.get('solvable'):
                                        expr_result['steps'] = (
                                            steps_result['steps']
                                        )
                            else:
                                expr_result['type'] = 'expression'

                        math_context['expressions'].append(expr_result)
                        math_metadata['expressions'].append(expr_str)

                    except Exception as e:
                        logger.warning(
                            f"Error processing expression '{expr_str}': {e}"
                        )
                        continue

                math_metadata['math_detected'] = True

        except Exception as e:
            logger.error(f"Error in math detection: {e}", exc_info=True)
            # Continue without math context - fallback to LLM only

        # Record computation time
        math_metadata['computation_time_ms'] = int(
            (time.time() - start_time) * 1000
        )

        # Generate Socratic response with validation and math context
        conversation_history = context_summary.get('recent_history')
        logger.info(f"[SOCKET] Passing conversation context to Socratic guard: {len(conversation_history)} characters")
        logger.debug(f"[SOCKET] Conversation history content: {conversation_history[:200] if conversation_history else 'EMPTY'}")

        # First detect if this is a final answer (before generating response)
        is_final_answer = socratic_guard.detect_final_answer(content, math_context)
        is_correct_answer = False

        if is_final_answer:
            logger.info(f"[STREAK] Detected final answer from student: {content}")

            # Validate the answer against the correct solution FIRST
            is_correct_answer, explanation, expected_answer = answer_checker.check_answer(
                student_message=content,
                conversation_history=conversation_history
            )

            logger.info(f"[ANSWER_CHECK] Validation result: {is_correct_answer}, {explanation}")

            if is_correct_answer:
                # Increment consecutive correct count for correct answers
                conversation.consecutive_correct_count += 1
                db.session.add(conversation)

                current_streak = conversation.consecutive_correct_count
                logger.info(f"[STREAK] Correct answer! Updated streak to {current_streak}")

                # Check if celebration should be triggered (every 3 correct answers)
                if current_streak > 0 and current_streak % 3 == 0:
                    celebration_result = celebration_service.update_streak(
                        conversation_id=conversation_id,
                        is_correct=True,
                        current_streak=current_streak - 1  # subtract 1 since update_streak will add 1
                    )

                    if celebration_result['celebration_triggered']:
                        logger.info(f"[CELEBRATION] Triggered for streak {current_streak}")
            else:
                # Reset streak on incorrect answer
                logger.info(f"[STREAK] Incorrect answer. Resetting streak to 0")
                conversation.consecutive_correct_count = 0
                db.session.add(conversation)

        # Now generate the tutor response with answer correctness info
        result = socratic_guard.generate_validated_response(
            student_message=content,
            conversation_context=conversation_history,
            math_context=math_context,
            is_correct_answer=is_correct_answer if is_final_answer else None
        )

        # Use the tutor response directly - GPT-4o-mini handles encouragement naturally
        # Prepending encouragement every time makes responses repetitive
        tutor_content = result['response']
        is_final_answer = result.get('is_final_answer', is_final_answer)

        # Save tutor response with math metadata
        tutor_message = Message(
            conversation_id=conv_uuid,
            role=MessageRole.TUTOR,
            content=tutor_content,
            message_metadata={
                'validation_passed': result['validation_passed'],
                'attempts': result['attempts'],
                'confidence': result['confidence'],
                'socratic_guard_enabled': True,
                'math_context': math_metadata,
                'is_final_answer': is_final_answer
            }
        )
        db.session.add(tutor_message)
        db.session.commit()

        logger.info(
            f"Generated tutor response {tutor_message.id} "
            f"(validated: {result['validation_passed']}, attempts: {result['attempts']}, "
            f"is_final_answer: {is_final_answer})"
        )

        # Send tutor response
        response_data = tutor_message.to_dict()
        if is_final_answer:
            response_data['streak'] = conversation.consecutive_correct_count
        emit('message:receive', response_data)

    except Exception as e:
        logger.error(f"Error handling message:send: {e}", exc_info=True)
        db.session.rollback()
        emit('message:error', {
            'error': 'Internal server error',
            'message_id': data.get('message_id')
        })


@socketio.on('answer:validate')
def handle_answer_validation(data):
    """Handle answer validation using SymPy and streak tracking.

    Expected data:
        - conversation_id: UUID of conversation
        - student_answer: Student's answer (string)
        - expected_answer: Expected correct answer (string, optional)
        - context: Optional context (equation, problem statement)
        - current_streak: Current streak count (optional)
    """
    try:
        conversation_id = data.get('conversation_id')
        student_answer = data.get('student_answer')
        expected_answer = data.get('expected_answer')
        context = data.get('context')
        current_streak = data.get('current_streak', 0)

        # Validation
        if not conversation_id:
            logger.error("answer:validate without conversation_id")
            emit('answer:validation_error', {
                'error': 'Missing conversation_id'
            })
            return

        if not student_answer:
            logger.error("answer:validate without student_answer")
            emit('answer:validation_error', {
                'error': 'Missing student_answer'
            })
            return

        # Use AnswerValidator if expected answer provided
        validation_result = None
        is_correct = False

        if expected_answer:
            logger.info(
                f"Validating answer: '{student_answer}' vs '{expected_answer}'"
            )

            validation_result = answer_validator.validate_answer(
                student_answer=student_answer,
                expected_answer=expected_answer,
                context=context
            )

            is_correct = validation_result.get('correct', False)

            logger.info(
                f"Validation result: correct={is_correct}, "
                f"explanation={validation_result.get('explanation')}"
            )
        else:
            # If no expected answer, check if client provided is_correct
            is_correct = data.get('is_correct', False)
            logger.info(
                f"No expected answer provided, using client is_correct="
                f"{is_correct}"
            )

        # Update streak and check for celebration
        streak_result = celebration_service.update_streak(
            conversation_id=str(conversation_id),
            is_correct=is_correct,
            current_streak=current_streak
        )

        logger.info(
            f"Streak updated for {conversation_id}: "
            f"new_streak={streak_result['new_streak']}, "
            f"celebration={streak_result['celebration_triggered']}"
        )

        # Build response
        response = {
            'conversation_id': conversation_id,
            'is_correct': is_correct,
            'new_streak': streak_result['new_streak'],
            'celebration_triggered': streak_result['celebration_triggered']
        }

        # Add validation details if SymPy was used
        if validation_result:
            response['validation'] = {
                'correct': validation_result['correct'],
                'student_answer': validation_result['student_answer'],
                'expected_answer': validation_result['expected_answer'],
                'explanation': validation_result['explanation'],
                'is_approximate': validation_result.get(
                    'is_approximate', False
                )
            }

        # Send validation result back to client
        emit('answer:validated', response)

    except Exception as e:
        logger.error(f"Error handling answer:validate: {e}", exc_info=True)
        emit('answer:validation_error', {
            'error': 'Failed to validate answer',
            'conversation_id': data.get('conversation_id')
        })
