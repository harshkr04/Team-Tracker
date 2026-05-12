from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import Task, Project, ActivityLog
from extensions import db

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    # get tasks based on role - use database counts instead of loading all into memory
    if current_user.is_admin():
        total = Task.query.count()
        completed = Task.query.filter_by(status='completed').count()
        in_progress = Task.query.filter_by(status='in_progress').count()
        pending = Task.query.filter_by(status='pending').count()
        all_tasks = Task.query.all()  # needed for overdue check (date logic)
        overdue = sum(1 for t in all_tasks if t.is_overdue())
        projects = Project.query.filter(Project.status != 'archived').all()
        recent_tasks = Task.query.order_by(Task.created_at.desc()).limit(5).all()
    else:
        total = Task.query.filter_by(assigned_to=current_user.id).count()
        completed = Task.query.filter_by(assigned_to=current_user.id, status='completed').count()
        in_progress = Task.query.filter_by(assigned_to=current_user.id, status='in_progress').count()
        pending = Task.query.filter_by(assigned_to=current_user.id, status='pending').count()
        user_tasks = Task.query.filter_by(assigned_to=current_user.id).all()
        overdue = sum(1 for t in user_tasks if t.is_overdue())
        projects = current_user.projects
        recent_tasks = Task.query.filter_by(assigned_to=current_user.id).order_by(Task.created_at.desc()).limit(5).all()
    
    # recent activity (last 8 entries)
    recent_activity = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(8).all()
    
    return render_template('dashboard.html', 
        total=total,
        completed=completed,
        in_progress=in_progress,
        overdue=overdue,
        pending=pending,
        projects=projects,
        recent_tasks=recent_tasks,
        recent_activity=recent_activity
    )
