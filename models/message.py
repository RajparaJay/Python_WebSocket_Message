from datetime import datetime
from models import db


class Message(db.Model):
    """Message model for private and group messages."""
    
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=True, index=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<Message {self.id} from User {self.sender_id}>'
    
    def to_dict(self):
        """Convert message to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'sender_username': self.sender.username if self.sender else None,
            'receiver_email': self.receiver.email if self.receiver else None,
            'group_id': self.group_id,
            'content': self.content,
            'timestamp': self.timestamp.isoformat()
        }
