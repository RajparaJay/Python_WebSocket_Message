from models import db


class Group(db.Model):
    """Group model for group chats."""
    
    __tablename__ = 'groups'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    
    # Relationships
    members = db.relationship('GroupMember', backref='group', lazy='dynamic', 
                             cascade='all, delete-orphan')
    messages = db.relationship('Message', backref='group', lazy='dynamic',
                              cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Group {self.name}>'
    
    def to_dict(self):
        """Convert group to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'name': self.name
        }
