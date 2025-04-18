from flask import session
from flask_socketio import emit, join_room, leave_room
from models import db, Message, Contact, Group, GroupMember, User

def register_socket_events(socketio):
    @socketio.on('connect')
    def handle_connect():
        # Authenticate the connection
        if 'user_id' not in session:
            return False  # Reject connection
        
        user_id = session['user_id']
        
        # Join user's personal room for direct messages
        join_room(f"user_{user_id}")
        
        # Join all groups the user is a member of
        group_memberships = GroupMember.query.filter_by(user_id=user_id).all()
        for membership in group_memberships:
            join_room(f"group_{membership.group_id}")
        
        return True
    
    @socketio.on('disconnect')
    def handle_disconnect():
        pass  # We could clean up resources here if needed
    
    @socketio.on('send_message')
    def handle_send_message(data):
        if 'user_id' not in session:
            return {'success': False, 'message': 'Not authenticated'}
        
        user_id = session['user_id']
        message_text = data.get('message')
        receiver_id = data.get('receiver_id')
        group_id = data.get('group_id')
        
        if not message_text:
            return {'success': False, 'message': 'Message text is required'}
        
        # Create and save message (similar to your existing API)
        if group_id:
            # Check if user is a member of the group
            is_member = GroupMember.query.filter_by(group_id=group_id, user_id=user_id).first()
            if not is_member:
                return {'success': False, 'message': 'Not a member of this group'}
            
            # Create group message
            new_message = Message(
                sender_id=user_id,
                receiver_id=user_id,  # Placeholder for group messages
                message_text=message_text,
                is_group_message=True,
                group_id=group_id
            )
            
            db.session.add(new_message)
            db.session.commit()
            
            # Format the message for sending
            sender = User.query.get(user_id)
            message_data = {
                'id': new_message.id,
                'sender_id': user_id,
                'sender_username': sender.username,
                'message': message_text,
                'timestamp': new_message.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                'is_own_message': True, # This will be False for recipients
                'edited': False,
                'group_id': group_id
            }
            
            # Emit to the group room (including sender)
            emit('new_message', message_data, room=f"group_{group_id}")
            
            return {'success': True, 'message': message_data}
            
        elif receiver_id:
            # Direct message
            receiver = User.query.get(receiver_id)
            if not receiver:
                return {'success': False, 'message': 'Receiver not found'}
            
            # Create direct message
            new_message = Message(
                sender_id=user_id,
                receiver_id=receiver_id,
                message_text=message_text,
                is_group_message=False
            )
            
            db.session.add(new_message)
            db.session.commit()
            
            # Format the message
            sender = User.query.get(user_id)
            message_data = {
                'id': new_message.id,
                'sender_id': user_id,
                'sender_username': sender.username,
                'message': message_text,
                'timestamp': new_message.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                'is_own_message': True, # Will be False for receiver
                'edited': False
            }
            
            # Send to sender
            emit('new_message', message_data, room=f"user_{user_id}")
            
            # Modify is_own_message for receiver and send
            message_data['is_own_message'] = False
            emit('new_message', message_data, room=f"user_{receiver_id}")
            
            return {'success': True, 'message': message_data}
        
        return {'success': False, 'message': 'Invalid message data'}
    
    @socketio.on('update_lists')
    def handle_update_lists():
        """Emit updated contacts and groups lists to the requesting user"""
        if 'user_id' not in session:
            return {'success': False, 'message': 'Not authenticated'}
        
        user_id = session['user_id']
        
        # Get contacts (similar to your API)
        contacts_data = db.session.query(
            User, Contact.display_name
        ).join(
            Contact, Contact.contact_id == User.id
        ).filter(
            Contact.user_id == user_id
        ).all()
        
        contacts = [
            {
                "id": user.id,
                "username": user.username,
                "display_name": display_name or user.username
            }
            for user, display_name in contacts_data
        ]
        
        # Get groups
        user_groups = db.session.query(
            Group, GroupMember.is_admin
        ).join(
            GroupMember, GroupMember.group_id == Group.id
        ).filter(
            GroupMember.user_id == user_id
        ).all()
        
        groups = [
            {
                "id": group.id,
                "name": group.name,
                "is_admin": is_admin,
                "created_by": group.created_by
            }
            for group, is_admin in user_groups
        ]
        
        # Emit the lists to the user's room
        emit('contacts_list', {'success': True, 'contacts': contacts}, room=f"user_{user_id}")
        emit('groups_list', {'success': True, 'groups': groups}, room=f"user_{user_id}")
        
        return {'success': True}

    # Broadcast when a contact is added, updated, or deleted
    @socketio.on('contact_changed')
    def handle_contact_changed(data):
        """Notify affected users about contact changes"""
        if 'user_id' not in session:
            return {'success': False, 'message': 'Not authenticated'}
        
        user_id = session['user_id']
        contact_id = data.get('contact_id')
        
        if contact_id:
            # Trigger list update for both users
            emit('trigger_update_lists', room=f"user_{user_id}")
            emit('trigger_update_lists', room=f"user_{contact_id}")
        
        return {'success': True}
    
    # Broadcast when a group is changed
    @socketio.on('group_changed')
    def handle_group_changed(data):
        """Notify affected users about group changes"""
        if 'user_id' not in session:
            return {'success': False, 'message': 'Not authenticated'}
        
        group_id = data.get('group_id')
        
        if group_id:
            # Get all members of the group
            members = GroupMember.query.filter_by(group_id=group_id).all()
            
            # Trigger list update for all members
            for member in members:
                emit('trigger_update_lists', room=f"user_{member.user_id}")
        
        return {'success': True} 