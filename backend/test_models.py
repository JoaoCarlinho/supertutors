"""Quick test script to verify database models work correctly."""
import sys
from app import create_app
from app.extensions import db
from app.models import Conversation, Message, MessageRole

def test_crud():
    """Test basic CRUD operations."""
    app = create_app()

    with app.app_context():
        # Create a conversation
        print("Creating conversation...")
        conv = Conversation(title="Test Math Problem")
        db.session.add(conv)
        db.session.commit()
        print(f"Created: {conv}")

        # Create messages
        print("\nCreating messages...")
        msg1 = Message(
            conversation_id=conv.id,
            role=MessageRole.STUDENT,
            content="I don't understand quadratic equations",
            message_metadata={"topic": "algebra"}
        )
        msg2 = Message(
            conversation_id=conv.id,
            role=MessageRole.TUTOR,
            content="Let's explore quadratic equations together. What specifically confuses you?",
            message_metadata={"strategy": "socratic"}
        )
        db.session.add_all([msg1, msg2])
        db.session.commit()
        print(f"Created: {msg1}")
        print(f"Created: {msg2}")

        # Read conversation with messages
        print("\nReading conversation with messages...")
        conv_from_db = db.session.get(Conversation, conv.id)
        print(f"Found conversation: {conv_from_db}")
        print(f"Messages count: {conv_from_db.messages.count()}")
        for msg in conv_from_db.messages:
            print(f"  - {msg}")

        # Update conversation title
        print("\nUpdating conversation title...")
        conv_from_db.title = "Quadratic Equations Help"
        db.session.commit()
        print(f"Updated: {conv_from_db}")

        # Test to_dict methods
        print("\nTesting to_dict serialization...")
        print(f"Conversation dict: {conv_from_db.to_dict()}")
        print(f"Message dict: {msg1.to_dict()}")

        # Delete conversation (should cascade to messages)
        print("\nDeleting conversation (cascade delete messages)...")
        db.session.delete(conv_from_db)
        db.session.commit()

        # Verify messages are deleted
        remaining_messages = db.session.query(Message).filter_by(conversation_id=conv.id).count()
        print(f"Remaining messages after cascade delete: {remaining_messages}")

        print("\n✅ All CRUD operations successful!")

if __name__ == '__main__':
    try:
        test_crud()
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
