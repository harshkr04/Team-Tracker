from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import Task, Project, User, Comment, ActivityLog
from extensions import db
from datetime import datetime

tasks_bp = Blueprint('tasks', __name__, url_prefix='/tasks')

VALID_PRIORITIES = {'low', 'medium', 'high'}
VALID_STATUSES = {'pending', 'in_progress', 'completed'}

@tasks_bp.route('/')
@login_required
def list_tasks():
    """show tasks with filtering, sorting, search, and pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = 15
    
    # base query
    if current_user.is_admin():
        query = Task.query
    else:
        query = Task.query.filter_by(assigned_to=current_user.id)
    
    # --- Filters ---
    status_filter = request.args.get('status', '')
    priority_filter = request.args.get('priority', '')
    project_filter = request.args.get('project_id', '', type=str)
    search_query = request.args.get('q', '').strip()
    sort_by = request.args.get('sort', 'created')
    
    if status_filter and status_filter in VALID_STATUSES:
        query = query.filter_by(status=status_filter)
    
    if priority_filter and priority_filter in VALID_PRIORITIES:
        query = query.filter_by(priority=priority_filter)
    
    if project_filter:
        query = query.filter_by(project_id=int(project_filter))
    
    if search_query:
        query = query.filter(Task.title.ilike(f'%{search_query}%'))
    
    # --- Sorting ---
    if sort_by == 'due_date':
        query = query.order_by(Task.due_date.asc().nullslast())
    elif sort_by == 'priority':
        # custom order: high > medium > low
        from sqlalchemy import case
        priority_order = case(
            (Task.priority == 'high', 1),
            (Task.priority == 'medium', 2),
            (Task.priority == 'low', 3),
            else_=2
        )
        query = query.order_by(priority_order)
    else:
        query = query.order_by(Task.created_at.desc())
    
    # --- Pagination ---
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    tasks = pagination.items
    
    # get projects for filter dropdown
    projects = Project.query.all()
    
    return render_template('tasks.html', 
        tasks=tasks, 
        pagination=pagination,
        projects=projects,
        filters={
            'status': status_filter,
            'priority': priority_filter,
            'project_id': project_filter,
            'q': search_query,
            'sort': sort_by
        }
    )

@tasks_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_task():
    if not current_user.is_admin():
        flash('Only admins can create tasks', 'error')
        return redirect(url_for('tasks.list_tasks'))
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        project_id = request.form.get('project_id')
        assigned_to = request.form.get('assigned_to')
        priority = request.form.get('priority', 'medium')
        due_date_str = request.form.get('due_date', '')
        
        # validation
        if not title:
            flash('Task title is required', 'error')
            return redirect(url_for('tasks.create_task'))
        
        if not project_id:
            flash('Please select a project', 'error')
            return redirect(url_for('tasks.create_task'))
        
        # validate priority
        if priority not in VALID_PRIORITIES:
            priority = 'medium'
        
        # parse due date
        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format', 'error')
                return redirect(url_for('tasks.create_task'))
        
        try:
            task = Task(
                title=title,
                description=description,
                project_id=int(project_id),
                assigned_to=int(assigned_to) if assigned_to else None,
                due_date=due_date,
                status='pending',
                priority=priority
            )
            db.session.add(task)
            
            # log activity
            assignee_name = ''
            if assigned_to:
                assignee = User.query.get(int(assigned_to))
                assignee_name = f' → {assignee.username}' if assignee else ''
            ActivityLog.log(current_user.id, 'created', 'task', title, 
                          f'Priority: {priority}{assignee_name}')
            
            db.session.commit()
            
            flash('Task created!', 'success')
            return redirect(url_for('projects.view_project', project_id=project_id))
        except Exception as e:
            db.session.rollback()
            flash('Error creating task', 'error')
            print(f"Task create error: {e}")
            return redirect(url_for('tasks.create_task'))
    
    # GET - show form
    projects = Project.query.filter(Project.status != 'archived').all()
    users = User.query.all()
    
    # check if project_id was passed as query param
    preselected_project = request.args.get('project_id')
    
    return render_template('create_task.html', projects=projects, users=users, preselected_project=preselected_project)

@tasks_bp.route('/<int:task_id>')
@login_required
def view_task(task_id):
    """Task detail page with comments"""
    task = Task.query.get_or_404(task_id)
    
    # check access: admin or assigned user or project member
    is_member = current_user.is_admin() or task.assigned_to == current_user.id or \
                current_user in task.project.members
    
    return render_template('view_task.html', task=task, is_member=is_member)

@tasks_bp.route('/<int:task_id>/comment', methods=['POST'])
@login_required
def add_comment(task_id):
    """Add a comment to a task"""
    task = Task.query.get_or_404(task_id)
    
    # check access
    is_member = current_user.is_admin() or task.assigned_to == current_user.id or \
                current_user in task.project.members
    if not is_member:
        flash('You do not have access to comment on this task', 'error')
        return redirect(url_for('tasks.list_tasks'))
    
    content = request.form.get('content', '').strip()
    if not content:
        flash('Comment cannot be empty', 'error')
        return redirect(url_for('tasks.view_task', task_id=task_id))
    
    try:
        comment = Comment(
            content=content,
            task_id=task_id,
            user_id=current_user.id
        )
        db.session.add(comment)
        
        # update task timestamp
        task.updated_at = datetime.utcnow()
        
        # log activity
        ActivityLog.log(current_user.id, 'commented', 'task', task.title,
                       content[:100])
        
        db.session.commit()
        flash('Comment added', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error adding comment', 'error')
        print(f"Comment error: {e}")
    
    return redirect(url_for('tasks.view_task', task_id=task_id))

@tasks_bp.route('/<int:task_id>/update-status', methods=['POST'])
@login_required
def update_status(task_id):
    task = Task.query.get_or_404(task_id)
    
    # members can only update their own tasks
    if not current_user.is_admin() and task.assigned_to != current_user.id:
        flash('You can only update your own tasks', 'error')
        return redirect(url_for('tasks.list_tasks'))
    
    new_status = request.form.get('status')
    
    if new_status not in VALID_STATUSES:
        flash('Invalid status', 'error')
        return redirect(url_for('tasks.list_tasks'))
    
    old_status = task.status
    task.status = new_status
    task.updated_at = datetime.utcnow()
    
    # log activity
    ActivityLog.log(current_user.id, 'updated', 'task', task.title,
                   f'Status: {old_status} → {new_status}')
    
    db.session.commit()
    flash('Task status updated!', 'success')
    
    # redirect back to where they came from
    next_url = request.form.get('next', url_for('tasks.list_tasks'))
    return redirect(next_url)

@tasks_bp.route('/<int:task_id>/delete', methods=['POST'])
@login_required
def delete_task(task_id):
    if not current_user.is_admin():
        flash('Only admins can delete tasks', 'error')
        return redirect(url_for('tasks.list_tasks'))
    
    task = Task.query.get_or_404(task_id)
    proj_id = task.project_id
    task_title = task.title
    
    try:
        db.session.delete(task)
        ActivityLog.log(current_user.id, 'deleted', 'task', task_title)
        db.session.commit()
        flash('Task deleted', 'success')
    except Exception:
        db.session.rollback()
        flash('Could not delete task', 'error')
    
    return redirect(url_for('projects.view_project', project_id=proj_id))
