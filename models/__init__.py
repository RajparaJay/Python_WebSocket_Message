from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy
db = SQLAlchemy()

# Import models to make them available when importing from models package
from models.user import User
from models.message import Message
from models.group import Group
from models.group_member import GroupMember

__all__ = ['db', 'User', 'Message', 'Group', 'GroupMember']
