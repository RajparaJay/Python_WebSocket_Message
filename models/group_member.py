from datetime import datetime
from models import db


class GroupMember(db.Model):
    """Group membership model with soft-delete functionality."""
    
    __tablename__ = 'group_members'
    
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    has_left = db.Column(db.Boolean, default=False, nullable=False)
    left_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<GroupMember User:{self.user_id} Group:{self.group_id}>'
    
    def leave_group(self):
        """Mark the member as having left the group."""
        self.has_left = True
        self.left_at = datetime.utcnow()
