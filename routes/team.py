from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from models import User, ActivityLog
from extensions import db

team_bp = Blueprint('team', __name__, url_prefix='/team')

@team_bp.route('/')
@login_required
def team_page():
    users = User.query.order_by(User.role.desc(), User.username).all()
    return render_template('team.html', users=users)

@team_bp.route('/add', methods=['POST'])
@login_required
def add_member():
    if not current_user.is_admin():
        flash('Only admins can add members', 'error')
        return redirect(url_for('team.team_page'))
    
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    
    if not username or not email or not password:
        flash('All fields are required', 'error')
        return redirect(url_for('team.team_page'))
    
    if User.query.filter_by(email=email).first():
        flash('Email already registered', 'error')
        return redirect(url_for('team.team_page'))
    
    if User.query.filter_by(username=username).first():
        flash('Username already taken', 'error')
        return redirect(url_for('team.team_page'))
    
    try:
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            role='member'
        )
        db.session.add(new_user)
        ActivityLog.log(current_user.id, 'added', 'member', username, f'Email: {email}')
        db.session.commit()
        flash(f'Member "{username}" added!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error adding member', 'error')
        print(f"Add member error: {e}")
    
    return redirect(url_for('team.team_page'))

@team_bp.route('/remove/<int:user_id>', methods=['POST'])
@login_required
def remove_member(user_id):
    if not current_user.is_admin():
        flash('Only admins can remove members', 'error')
        return redirect(url_for('team.team_page'))
    
    if user_id == current_user.id:
        flash('You cannot remove yourself', 'error')
        return redirect(url_for('team.team_page'))
    
    user = User.query.get_or_404(user_id)
    
    if user.is_admin():
        flash('Cannot remove another admin', 'error')
        return redirect(url_for('team.team_page'))
    
    try:
        username = user.username
        # remove from all projects first
        user.projects.clear()
        # reassign tasks
        for task in user.assigned_tasks:
            task.assigned_to = None
        db.session.delete(user)
        ActivityLog.log(current_user.id, 'removed', 'member', username)
        db.session.commit()
        flash(f'Member "{username}" removed', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error removing member', 'error')
        print(f"Remove member error: {e}")
    
    return redirect(url_for('team.team_page'))
