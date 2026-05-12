from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import Project, User, Task, ActivityLog
from extensions import db
from datetime import datetime

projects_bp = Blueprint('projects', __name__, url_prefix='/projects')

@projects_bp.route('/')
@login_required
def list_projects():
    # show active projects, with archived separate
    active_projects = Project.query.filter(Project.status != 'archived').all()
    archived_projects = Project.query.filter_by(status='archived').all()
    return render_template('projects.html', projects=active_projects, archived_projects=archived_projects)

@projects_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_project():
    # only admins can create projects
    if not current_user.is_admin():
        flash('Only admins can create projects', 'error')
        return redirect(url_for('projects.list_projects'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        deadline_str = request.form.get('deadline', '')
        member_ids = request.form.getlist('members')
        
        if not name:
            flash('Project name is required', 'error')
            return render_template('create_project.html', users=User.query.all())
        
        # parse deadline
        deadline = None
        if deadline_str:
            try:
                deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format', 'error')
                return render_template('create_project.html', users=User.query.all())
        
        try:
            project = Project(
                name=name,
                description=description,
                created_by=current_user.id,
                deadline=deadline
            )
            
            # add selected members
            for mid in member_ids:
                user = User.query.get(int(mid))
                if user:
                    project.members.append(user)
            
            # always add the creator as member too
            if current_user not in project.members:
                project.members.append(current_user)
            
            db.session.add(project)
            
            # log activity
            ActivityLog.log(current_user.id, 'created', 'project', name,
                          f'{len(member_ids)+1} members')
            
            db.session.commit()
            
            flash('Project created!', 'success')
            return redirect(url_for('projects.view_project', project_id=project.id))
        except Exception as e:
            db.session.rollback()
            flash('Error creating project', 'error')
            print(f"Error: {e}")
    
    users = User.query.all()
    return render_template('create_project.html', users=users)

@projects_bp.route('/<int:project_id>')
@login_required
def view_project(project_id):
    project = Project.query.get_or_404(project_id)
    
    # everyone can VIEW projects now (read-only for non-members)
    is_member = current_user.is_admin() or current_user in project.members
    
    tasks = Task.query.filter_by(project_id=project.id).all()
    all_users = User.query.all()
    return render_template('view_project.html', project=project, tasks=tasks, all_users=all_users, is_member=is_member)

@projects_bp.route('/<int:project_id>/add-member', methods=['POST'])
@login_required
def add_member(project_id):
    if not current_user.is_admin():
        flash('Only admins can add members', 'error')
        return redirect(url_for('projects.view_project', project_id=project_id))
    
    project = Project.query.get_or_404(project_id)
    user_id = request.form.get('user_id')
    
    if user_id:
        user = User.query.get(int(user_id))
        if user and user not in project.members:
            project.members.append(user)
            ActivityLog.log(current_user.id, 'added', 'member', user.username,
                          f'Added to {project.name}')
            db.session.commit()
            flash(f'Added {user.username} to project', 'success')
        else:
            flash('User already in project or not found', 'error')
    
    return redirect(url_for('projects.view_project', project_id=project_id))

@projects_bp.route('/<int:project_id>/archive', methods=['POST'])
@login_required
def archive_project(project_id):
    """Archive or unarchive a project"""
    if not current_user.is_admin():
        flash('Only admins can archive projects', 'error')
        return redirect(url_for('projects.list_projects'))
    
    project = Project.query.get_or_404(project_id)
    
    if project.status == 'archived':
        project.status = 'active'
        ActivityLog.log(current_user.id, 'restored', 'project', project.name)
        flash(f'Project "{project.name}" restored', 'success')
    else:
        project.status = 'archived'
        ActivityLog.log(current_user.id, 'archived', 'project', project.name)
        flash(f'Project "{project.name}" archived', 'success')
    
    db.session.commit()
    return redirect(url_for('projects.list_projects'))

@projects_bp.route('/<int:project_id>/delete', methods=['POST'])
@login_required
def delete_project(project_id):
    if not current_user.is_admin():
        flash('Only admins can delete projects', 'error')
        return redirect(url_for('projects.list_projects'))
    
    project = Project.query.get_or_404(project_id)
    project_name = project.name
    
    try:
        db.session.delete(project)
        ActivityLog.log(current_user.id, 'deleted', 'project', project_name)
        db.session.commit()
        flash('Project deleted', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting project', 'error')
        print(f"Delete error: {e}")
    
    return redirect(url_for('projects.list_projects'))
