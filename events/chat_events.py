from flask import request
from flask_login import current_user
from flask_socketio import emit, join_room, leave_room
from datetime import datetime
from models import db, User, Message, Group, GroupMember

# Track online users (user_id set)
online_users = set()
# Track socket_id -> user_data mapping
connected_users = {}


def register_chat_events(socketio):
    """Register all chat-related SocketIO events."""
    
    @socketio.on('connect')
    def handle_connect():
        """Handle user connection and auto-join their groups."""
        if not current_user.is_authenticated:
            return False
        
        # Join user's personal room for private messages
        join_room(f'user_{current_user.id}')
        
        # Join all groups the user is a member of (and hasn't left)
        memberships = GroupMember.query.filter_by(
            user_id=current_user.id,
            has_left=False
        ).all()
        
        for membership in memberships:
            join_room(f'group_{membership.group_id}')
        
        # Track user as online
        online_users.add(current_user.id)
        connected_users[request.sid] = {
            'user_id': current_user.id,
            'email': current_user.email,
            'username': current_user.username
        }
        
        # Broadcast online status to all users
        socketio.emit('user_online', {
            'user_id': current_user.id,
            'email': current_user.email
        })
        
        print(f'User {current_user.username} connected (SID: {request.sid})')
    
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle user disconnection."""
        # Get user data from tracked connections using SID
        user_data = connected_users.pop(request.sid, None)
        
        if user_data:
            user_id = user_data['user_id']
            email = user_data['email']
            username = user_data['username']
            
            # Remove user from online set
            # Only if they don't have other active connections (optional check, but simple discard is fine for now)
            # A more robust approach would count connections, but let's stick to simple presence
            # If user has multiple tabs open, we might want to keep them online.
            # But for now, let's just checking if any other SIDs map to this user
            
            # Check if user has other connections
            is_still_online = False
            for sid, data in connected_users.items():
                if data['user_id'] == user_id:
                    is_still_online = True
                    break
            
            if not is_still_online:
                online_users.discard(user_id)
                # Broadcast offline status to all users
                socketio.emit('user_offline', {
                    'user_id': user_id,
                    'email': email
                })
            
            print(f'User {username} disconnected (SID: {request.sid})')
    
    
    @socketio.on('logout_user')
    def handle_logout_user():
        """Handle explicit user logout signal."""
        if current_user.is_authenticated:
            # We don't remove from connected_users here, let disconnect handle that cleanup
            # But we DO mark them as offline immediately and broadcast
            
            # Check if this user has other connections that should keep them online?
            # For "logout", we assume they want to go offline everywhere or just this session.
            # But usually logout invalidates the session. 
            # So let's force offline.
            
            user_id = current_user.id
            email = current_user.email
            
            # Remove from online set
            online_users.discard(user_id)
            
            # Broadcast offline status
            socketio.emit('user_offline', {
                'user_id': user_id,
                'email': email
            })
            
            print(f'User {current_user.username} logged out explicitly (SID: {request.sid})')
    
    
    @socketio.on('send_message')
    def handle_send_message(data):
        """Handle broadcast message (legacy/global chat)."""
        if not current_user.is_authenticated:
            return
        
        message = data.get('message', '')
        emit('receive_message', {
            'user': current_user.username,
            'message': message
        }, broadcast=True)
    
    
    @socketio.on('send_private_message')
    def handle_send_private_message(data):
        """Handle private message between two users."""
        if not current_user.is_authenticated:
            return
        
        receiver_email = data.get('receiver_email')
        message_content = data.get('message')
        
        if not receiver_email or not message_content:
            emit('error', {'message': 'Invalid message data'})
            return
        
        receiver = User.query.filter_by(email=receiver_email).first()
        if not receiver:
            emit('error', {'message': 'Receiver not found'})
            return
        
        # Save message to database
        message = Message(
            sender_id=current_user.id,
            receiver_id=receiver.id,
            content=message_content,
            timestamp=datetime.utcnow()
        )
        db.session.add(message)
        db.session.commit()
        
        # Send to receiver
        socketio.emit('receive_private_message', {
            'username': current_user.username,
            'sender_email': current_user.email,
            'receiver_email': receiver_email,
            'message': message_content,
            'timestamp': message.timestamp.isoformat(),
            'is_own': False  # This is for the receiver
        }, room=f'user_{receiver.id}')
        
        # Send to sender (for confirmation)
        emit('receive_private_message', {
            'username': current_user.username,
            'sender_email': current_user.email,
            'receiver_email': receiver_email,
            'message': message_content,
            'timestamp': message.timestamp.isoformat(),
            'is_own': True  # This is for the sender
        })
    
    
    @socketio.on('create_group')
    def handle_create_group(data):
        """Handle group creation."""
        if not current_user.is_authenticated:
            return
        
        group_name = data.get('group_name')
        user_emails = data.get('user_emails', [])
        
        if not group_name:
            emit('error', {'message': 'Group name is required'})
            return
        
        # Create group
        group = Group(name=group_name)
        db.session.add(group)
        db.session.flush()  # Get the group ID
        
        # Add creator as member
        creator_membership = GroupMember(
            group_id=group.id,
            user_id=current_user.id
        )
        db.session.add(creator_membership)
        
        # Add other members
        member_ids = [current_user.id]
        for email in user_emails:
            user = User.query.filter_by(email=email).first()
            if user and user.id != current_user.id:
                membership = GroupMember(
                    group_id=group.id,
                    user_id=user.id
                )
                db.session.add(membership)
                member_ids.append(user.id)
        
        db.session.commit()
        
        # Notify all members about the new group
        for user_id in member_ids:
            socketio.emit('group_created', {
                'group_id': group.id,
                'group_name': group_name,
                'is_creator': user_id == current_user.id  # Only true for the creator
            }, room=f'user_{user_id}')
        
        # Join the creator to the group room
        join_room(f'group_{group.id}')
    
    
    @socketio.on('send_group_message')
    def handle_send_group_message(data):
        """Handle group message."""
        if not current_user.is_authenticated:
            return
        
        group_id = data.get('group_id')
        message_content = data.get('message')
        
        if not group_id or not message_content:
            emit('error', {'message': 'Invalid message data'})
            return
        
        # Verify membership and that user hasn't left
        membership = GroupMember.query.filter_by(
            group_id=group_id,
            user_id=current_user.id,
            has_left=False
        ).first()
        
        if not membership:
            emit('error', {'message': 'You are not a member of this group'})
            return
        
        # Save message to database
        message = Message(
            sender_id=current_user.id,
            group_id=group_id,
            content=message_content,
            timestamp=datetime.utcnow()
        )
        db.session.add(message)
        db.session.commit()
        
        # Broadcast to group
        socketio.emit('receive_group_message', {
            'group_id': group_id,
            'username': current_user.username,
            'sender_email': current_user.email,
            'message': message_content,
            'timestamp': message.timestamp.isoformat()
        }, room=f'group_{group_id}')
    
    
    @socketio.on('leave_group')
    def handle_leave_group(data):
        """Handle user leaving a group (soft delete)."""
        if not current_user.is_authenticated:
            return
        
        group_id = data.get('group_id')
        
        if not group_id:
            emit('error', {'message': 'Group ID is required'})
            return
        
        membership = GroupMember.query.filter_by(
            group_id=group_id,
            user_id=current_user.id
        ).first()
        
        if not membership:
            emit('error', {'message': 'You are not a member of this group'})
            return
        
        # Soft delete - mark as left
        membership.leave_group()
        db.session.commit()
        
        # Leave the SocketIO room
        leave_room(f'group_{group_id}')
        
        # Notify caller
        emit('group_left', {'group_id': group_id})
        
        # Notify group members
        socketio.emit('receive_group_message', {
            'group_id': group_id,
            'username': 'System',
            'message': f'{current_user.username} has left the group.',
            'timestamp': datetime.utcnow().isoformat()
        }, room=f'group_{group_id}')
    
    
    @socketio.on('delete_group_data')
    def handle_delete_group_data(data):
        """Handle permanent deletion of group membership data."""
        if not current_user.is_authenticated:
            return
        
        group_id = data.get('group_id')
        
        if not group_id:
            emit('error', {'message': 'Group ID is required'})
            return
        
        membership = GroupMember.query.filter_by(
            group_id=group_id,
            user_id=current_user.id,
            has_left=True
        ).first()
        
        if membership:
            db.session.delete(membership)
            db.session.commit()
            emit('group_data_deleted', {'group_id': group_id})
    
    
    @socketio.on('join_channel')
    def handle_join_channel(data):
        """Handle user joining a group channel."""
        if not current_user.is_authenticated:
            return
        
        group_id = data.get('group_id')
        
        if not group_id:
            emit('error', {'message': 'Group ID is required'})
            return
        
        # Verify membership and that user hasn't left
        membership = GroupMember.query.filter_by(
            group_id=group_id,
            user_id=current_user.id,
            has_left=False
        ).first()
        
        if membership:
            join_room(f'group_{group_id}')
            emit('joined_channel', {'group_id': group_id})
