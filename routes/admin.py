import json
from flask import Blueprint, jsonify, request, render_template, flash, redirect, url_for, session
from models import db, User, Message, Group, GroupMember, Contact, Setting

admin = Blueprint('admin', __name__)

@admin.route('/admin')
def admin_panel():
    # Check if user is logged in
    if 'user_id' not in session:
        flash('Please log in first')
        return redirect(url_for('auth.login_page'))
    
    # Check if user is an admin via session
    if not session.get('is_admin', False):
        flash('Access denied: Admin privileges required')
        return redirect(url_for('auth.login_page'))
    
    return render_template('admin.html')

# Admin API endpoints

@admin.route('/api/admin/stats/users', methods=['GET'])
def admin_user_stats():
    # Check if user is logged in and is admin
    if 'user_id' not in session or not session.get('is_admin', False):
        return jsonify(success=False, message="Access denied")
    
    try:
        # Get total user count
        user_count = User.query.count()
        return jsonify(success=True, count=user_count)
    except Exception as e:
        return jsonify(success=False, message=f"Failed to get user stats: {str(e)}")

@admin.route('/api/admin/stats/groups', methods=['GET'])
def admin_group_stats():
    # Check if user is logged in and is admin
    if 'user_id' not in session or not session.get('is_admin', False):
        return jsonify(success=False, message="Access denied")
    
    try:
        # Get total group count
        group_count = Group.query.count()
        return jsonify(success=True, count=group_count)
    except Exception as e:
        return jsonify(success=False, message=f"Failed to get group stats: {str(e)}")

@admin.route('/api/admin/stats/messages', methods=['GET'])
def admin_message_stats():
    # Check if user is logged in and is admin
    if 'user_id' not in session or not session.get('is_admin', False):
        return jsonify(success=False, message="Access denied")
    
    try:
        # Get total message count
        message_count = Message.query.count()
        return jsonify(success=True, count=message_count)
    except Exception as e:
        return jsonify(success=False, message=f"Failed to get message stats: {str(e)}")

@admin.route('/api/admin/users', methods=['GET'])
def admin_get_users():
    # Check if user is logged in and is admin
    if 'user_id' not in session or not session.get('is_admin', False):
        return jsonify(success=False, message="Access denied")
    
    try:
        # Get all users
        users = User.query.all()
        
        # Format user data
        user_list = []
        for user in users:
            user_list.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_admin': user.is_admin if hasattr(user, 'is_admin') else False,
                'is_banned': user.is_banned if hasattr(user, 'is_banned') else False
            })
        
        return jsonify(success=True, users=user_list)
    except Exception as e:
        return jsonify(success=False, message=f"Failed to get users: {str(e)}")

@admin.route('/api/admin/users/<int:user_id>/ban', methods=['POST'])
def admin_ban_user(user_id):
    # Check if user is logged in and is admin
    if 'user_id' not in session or not session.get('is_admin', False):
        return jsonify(success=False, message="Access denied")
    
    try:
        # Get user to ban
        user = User.query.get(user_id)
        
        if not user:
            return jsonify(success=False, message="User not found")
        
        # Cannot ban admin users
        if hasattr(user, 'is_admin') and user.is_admin:
            return jsonify(success=False, message="Cannot ban admin users")
        
        # Add is_banned field if it doesn't exist
        if not hasattr(user, 'is_banned'):
            return jsonify(success=False, message="User model doesn't support banning")
        
        # Ban user
        user.is_banned = True
        db.session.commit()
        
        return jsonify(success=True)
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, message=f"Failed to ban user: {str(e)}")

@admin.route('/api/admin/users/<int:user_id>/unban', methods=['POST'])
def admin_unban_user(user_id):
    # Check if user is logged in and is admin
    if 'user_id' not in session or not session.get('is_admin', False):
        return jsonify(success=False, message="Access denied")
    
    try:
        # Get user to unban
        user = User.query.get(user_id)
        
        if not user:
            return jsonify(success=False, message="User not found")
        
        # Check if is_banned field exists
        if not hasattr(user, 'is_banned'):
            return jsonify(success=False, message="User model doesn't support banning")
        
        # Unban user
        user.is_banned = False
        db.session.commit()
        
        return jsonify(success=True)
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, message=f"Failed to unban user: {str(e)}")

@admin.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
def admin_delete_user(user_id):
    # Check if user is logged in and is admin
    if 'user_id' not in session or not session.get('is_admin', False):
        return jsonify(success=False, message="Access denied")
    
    try:
        # Get user to delete
        user = User.query.get(user_id)
        
        if not user:
            return jsonify(success=False, message="User not found")
        
        # Cannot delete admin users
        if hasattr(user, 'is_admin') and user.is_admin:
            return jsonify(success=False, message="Cannot delete admin users")
        
        # Delete user's messages
        Message.query.filter_by(sender_id=user_id).delete()
        
        # Remove user from groups
        for membership in GroupMember.query.filter_by(user_id=user_id).all():
            db.session.delete(membership)
        
        # Delete user's contacts
        Contact.query.filter_by(user_id=user_id).delete()
        Contact.query.filter_by(contact_id=user_id).delete()
        
        # Delete user
        db.session.delete(user)
        db.session.commit()
        
        return jsonify(success=True)
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, message=f"Failed to delete user: {str(e)}")

@admin.route('/api/admin/settings/blocked-hashtags', methods=['GET'])
def admin_get_blocked_hashtags():
    # Check if user is logged in and is admin
    if 'user_id' not in session or not session.get('is_admin', False):
        return jsonify(success=False, message="Access denied")
    
    try:
        # Get blocked hashtags from settings
        setting = Setting.query.filter_by(key='blocked_hashtags').first()
        
        if setting:
            hashtags = json.loads(setting.value)
        else:
            hashtags = []
        
        return jsonify(success=True, hashtags=hashtags)
    except Exception as e:
        return jsonify(success=False, message=f"Failed to get blocked hashtags: {str(e)}")

@admin.route('/api/admin/settings/blocked-hashtags', methods=['POST'])
def admin_set_blocked_hashtags():
    # Check if user is logged in and is admin
    if 'user_id' not in session or not session.get('is_admin', False):
        return jsonify(success=False, message="Access denied")
    
    try:
        # Get hashtags from request
        data = request.get_json()
        
        if not data or 'hashtags' not in data:
            return jsonify(success=False, message="Invalid request")
        
        hashtags = data['hashtags']
        
        # Save hashtags to settings
        setting = Setting.query.filter_by(key='blocked_hashtags').first()
        
        if setting:
            setting.value = json.dumps(hashtags)
        else:
            setting = Setting(key='blocked_hashtags', value=json.dumps(hashtags))
            db.session.add(setting)
        
        db.session.commit()
        
        return jsonify(success=True)
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, message=f"Failed to set blocked hashtags: {str(e)}")

@admin.route('/api/admin/settings/ai-moderation', methods=['GET'])
def admin_get_ai_moderation():
    # Check if user is logged in and is admin
    if 'user_id' not in session or not session.get('is_admin', False):
        return jsonify(success=False, message="Access denied")
    
    try:
        # Get AI moderation setting
        setting = Setting.query.filter_by(key='ai_moderation_enabled').first()
        
        if setting:
            enabled = setting.value.lower() == 'true'
        else:
            enabled = False
        
        return jsonify(success=True, enabled=enabled)
    except Exception as e:
        return jsonify(success=False, message=f"Failed to get AI moderation setting: {str(e)}")

@admin.route('/api/admin/settings/ai-moderation', methods=['POST'])
def admin_set_ai_moderation():
    # Check if user is logged in and is admin
    if 'user_id' not in session or not session.get('is_admin', False):
        return jsonify(success=False, message="Access denied")
    
    try:
        # Get enabled status from request
        data = request.get_json()
        
        if not data or 'enabled' not in data:
            return jsonify(success=False, message="Invalid request")
        
        enabled = data['enabled']
        
        # Save setting
        setting = Setting.query.filter_by(key='ai_moderation_enabled').first()
        
        if setting:
            setting.value = str(enabled).lower()
        else:
            setting = Setting(key='ai_moderation_enabled', value=str(enabled).lower())
            db.session.add(setting)
        
        db.session.commit()
        
        return jsonify(success=True)
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, message=f"Failed to set AI moderation: {str(e)}") 