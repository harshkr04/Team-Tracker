from flask import Blueprint, render_template, request
from flask_login import login_required
from models import ActivityLog, User

activity_bp = Blueprint('activity', __name__, url_prefix='/activity')

@activity_bp.route('/')
@login_required
def activity_page():
    """Show activity log with filtering"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    query = ActivityLog.query
    
    # filter by user
    user_filter = request.args.get('user_id', '', type=str)
    if user_filter:
        query = query.filter_by(user_id=int(user_filter))
    
    # filter by action type
    action_filter = request.args.get('action', '')
    if action_filter:
        query = query.filter_by(action=action_filter)
    
    # filter by target type
    type_filter = request.args.get('type', '')
    if type_filter:
        query = query.filter_by(target_type=type_filter)
    
    query = query.order_by(ActivityLog.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    users = User.query.all()
    
    return render_template('activity.html', 
        activities=pagination.items, 
        pagination=pagination, 
        users=users,
        filters={
            'user_id': user_filter,
            'action': action_filter,
            'type': type_filter
        }
    )
