from flask import Flask, redirect, url_for, render_template_string
from extensions import db, login_manager, csrf
import os

def create_app():
    app = Flask(__name__)
    
    # config stuff
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'ethara-fallback-key-change-in-prod')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///teamtracker.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # import models so they get registered
    from models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # register blueprints
    from routes.auth import auth_bp
    from routes.projects import projects_bp
    from routes.tasks import tasks_bp
    from routes.dashboard import dashboard_bp
    from routes.settings import settings_bp
    from routes.team import team_bp
    from routes.activity import activity_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(team_bp)
    app.register_blueprint(activity_bp)
    
    @app.route('/')
    def index():
        return redirect(url_for('dashboard.dashboard'))
    
    # --- Global Error Handlers ---
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template_string(ERROR_PAGE, code=404, message="Page Not Found",
            detail="The page you're looking for doesn't exist."), 404

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return render_template_string(ERROR_PAGE, code=500, message="Internal Server Error",
            detail="Something went wrong on our end. Please try again."), 500

    @app.errorhandler(403)
    def forbidden(e):
        return render_template_string(ERROR_PAGE, code=403, message="Access Denied",
            detail="You don't have permission to access this page."), 403
    
    # create tables & run migrations
    with app.app_context():
        db.create_all()
        _auto_migrate(app)
        _create_default_admin(app)
    
    return app

# simple error page template
ERROR_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ code }} - Ethara.ai</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        * { margin:0; padding:0; box-sizing:border-box; }
        body { font-family:'Inter',sans-serif; background:#F9FAFB; display:flex;
               justify-content:center; align-items:center; min-height:100vh; }
        .error-box { text-align:center; padding:3rem; }
        .error-code { font-size:5rem; font-weight:700; color:#4338CA; line-height:1; }
        .error-msg { font-size:1.25rem; font-weight:600; color:#111827; margin:1rem 0 0.5rem; }
        .error-detail { color:#6B7280; margin-bottom:2rem; font-size:0.9375rem; }
        .error-btn { display:inline-block; padding:8px 20px; background:#4338CA; color:white;
                     text-decoration:none; border-radius:6px; font-weight:500; font-size:0.875rem; }
        .error-btn:hover { background:#3730A3; }
    </style>
</head>
<body>
    <div class="error-box">
        <div class="error-code">{{ code }}</div>
        <div class="error-msg">{{ message }}</div>
        <p class="error-detail">{{ detail }}</p>
        <a href="/" class="error-btn">Go to Dashboard</a>
    </div>
</body>
</html>
"""

def _auto_migrate(app):
    """Auto-add missing columns to existing SQLite tables."""
    import sqlite3
    
    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    if not db_path or not db_path.endswith('.db'):
        return  # skip for non-sqlite databases
    if not os.path.isabs(db_path):
        db_path = os.path.join(app.instance_path, db_path)
    
    if not os.path.exists(db_path):
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # --- Task table migrations ---
        cursor.execute("PRAGMA table_info(task)")
        task_cols = [row[1] for row in cursor.fetchall()]
        
        if 'priority' not in task_cols:
            print("[AUTO-MIGRATE] Adding 'priority' column to task table...")
            cursor.execute("ALTER TABLE task ADD COLUMN priority VARCHAR(20) DEFAULT 'medium'")
        
        if 'updated_at' not in task_cols:
            print("[AUTO-MIGRATE] Adding 'updated_at' column to task table...")
            cursor.execute("ALTER TABLE task ADD COLUMN updated_at DATETIME")
        
        # --- User table migrations ---
        cursor.execute("PRAGMA table_info(user)")
        user_cols = [row[1] for row in cursor.fetchall()]
        
        if 'last_active' not in user_cols:
            print("[AUTO-MIGRATE] Adding 'last_active' column to user table...")
            cursor.execute("ALTER TABLE user ADD COLUMN last_active DATETIME")
        
        if 'notify_email' not in user_cols:
            print("[AUTO-MIGRATE] Adding 'notify_email' column to user table...")
            cursor.execute("ALTER TABLE user ADD COLUMN notify_email BOOLEAN DEFAULT 1")
        
        if 'notify_tasks' not in user_cols:
            print("[AUTO-MIGRATE] Adding 'notify_tasks' column to user table...")
            cursor.execute("ALTER TABLE user ADD COLUMN notify_tasks BOOLEAN DEFAULT 1")
        
        # --- Project table migrations ---
        cursor.execute("PRAGMA table_info(project)")
        proj_cols = [row[1] for row in cursor.fetchall()]
        
        if 'deadline' not in proj_cols:
            print("[AUTO-MIGRATE] Adding 'deadline' column to project table...")
            cursor.execute("ALTER TABLE project ADD COLUMN deadline DATE")
        
        if 'status' not in proj_cols:
            print("[AUTO-MIGRATE] Adding 'status' column to project table...")
            cursor.execute("ALTER TABLE project ADD COLUMN status VARCHAR(20) DEFAULT 'active'")
        
        # --- Fix old status values ---
        cursor.execute("UPDATE task SET status='pending' WHERE status='todo'")
        cursor.execute("UPDATE task SET status='completed' WHERE status='done'")
        
        conn.commit()
        print("[AUTO-MIGRATE] All migrations applied.")
        
    except Exception as e:
        print(f"[AUTO-MIGRATE] Warning: {e}")
    finally:
        conn.close()

def _create_default_admin(app):
    """create a default admin account so we can test easily"""
    from models import User
    from werkzeug.security import generate_password_hash
    
    if not User.query.filter_by(email='admin@teamtracker.com').first():
        admin = User(
            username='admin',
            email='admin@teamtracker.com',
            password_hash=generate_password_hash('admin123'),
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        print("Created default admin account")

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
