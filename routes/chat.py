from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models import db, User, Message, Group, GroupMember
from sqlalchemy import or_, and_
from events.chat_events import online_users

chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')


@chat_bp.route('/users', methods=['GET'])
@login_required
def get_users():
    """Get all users except the current user."""
    users = User.query.filter(User.id != current_user.id).all()
    return jsonify([{
        'email': user.email,
        'username': user.username,
        'is_online': user.id in online_users
    } for user in users]), 200


@chat_bp.route('/groups', methods=['GET'])
@login_required
def get_groups():
    """Get all groups the current user is a member of."""
    memberships = GroupMember.query.filter_by(user_id=current_user.id).all()
    
    groups_data = []
    for membership in memberships:
        group = membership.group
        # Count active members (excluding current user)
        active_member_count = GroupMember.query.filter(
            and_(
                GroupMember.group_id == group.id,
                GroupMember.user_id != current_user.id,
                GroupMember.has_left == False
            )
        ).count()
        
        groups_data.append({
            'id': group.id,
            'name': group.name,
            'has_left': membership.has_left,
            'active_member_count': active_member_count
        })
    
    return jsonify(groups_data), 200


@chat_bp.route('/history/private/<string:other_email>', methods=['GET'])
@login_required
def get_private_history(other_email):
    """Get private message history with another user."""
    other_user = User.query.filter_by(email=other_email).first()
    
    if not other_user:
        return jsonify({'error': 'User not found'}), 404
    
    # Get messages between current user and other user
    messages = Message.query.filter(
        or_(
            and_(Message.sender_id == current_user.id, Message.receiver_id == other_user.id),
            and_(Message.sender_id == other_user.id, Message.receiver_id == current_user.id)
        )
    ).order_by(Message.timestamp).all()
    
    messages_data = [{
        'username': msg.sender.username,
        'sender_email': msg.sender.email,
        'content': msg.content,
        'timestamp': msg.timestamp.isoformat(),
        'is_own': msg.sender_id == current_user.id
    } for msg in messages]
    
    return jsonify(messages_data), 200


@chat_bp.route('/history/group/<int:group_id>', methods=['GET'])
@login_required
def get_group_history(group_id):
    """Get group message history, filtered by soft-leave timestamp."""
    # Verify membership
    membership = GroupMember.query.filter_by(
        group_id=group_id,
        user_id=current_user.id
    ).first()
    
    if not membership:
        return jsonify({'error': 'You are not a member of this group'}), 403
    
    # Build query for group messages
    query = Message.query.filter_by(group_id=group_id)
    
    # If user has left, only show messages before they left
    if membership.has_left and membership.left_at:
        query = query.filter(Message.timestamp <= membership.left_at)
    
    messages = query.order_by(Message.timestamp).all()
    
    messages_data = [{
        'username': msg.sender.username,
        'sender_email': msg.sender.email,
        'content': msg.content,
        'timestamp': msg.timestamp.isoformat(),
        'is_own': msg.sender_id == current_user.id
    } for msg in messages]
    
    return jsonify(messages_data), 200
