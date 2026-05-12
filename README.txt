================================================================================
                  ETHARA.AI - SMART WORK MANAGEMENT SYSTEM
================================================================================

A clean, role-based team task management web application built with Flask and
SQLAlchemy. Designed for small teams to manage projects, assign tasks, and
track progress through an intuitive dashboard.

Repository : https://github.com/harshkr04/Team-Tracker
Python     : >= 3.8
License    : Educational Purpose

================================================================================
                                 FEATURES
================================================================================

AUTHENTICATION & ROLES
  - Login / Signup with secure password hashing (Werkzeug)
  - Admin  : Full access - create projects, assign tasks, manage team
  - Member : View all projects, update assigned tasks, view team

DASHBOARD
  - Real-time stats: Total Tasks, Completed, In Progress, Overdue
  - Visual progress bar (percentage completed)
  - Project-wise task distribution chart
  - Recent tasks with priority badges

PROJECT MANAGEMENT
  - Create, view, and delete projects
  - Add/remove team members per project
  - Members can view all projects (read-only for unassigned)

TASK MANAGEMENT
  - Create tasks with title, description, priority, and due date
  - Assign tasks to team members
  - Status tracking: Pending -> In Progress -> Completed
  - Priority levels: High, Medium, Low
  - Automatic overdue detection

TEAM MANAGEMENT
  - View all team members with role badges and activity status
  - Admin can add or remove members
  - User avatar initials

SETTINGS
  - Profile       : Update username and email
  - Security      : Change password with validation
  - Notifications : Toggle email and task update preferences

UI / UX
  - Modern, minimal design with Inter font (Google Fonts)
  - Indigo (#4F46E5) color palette
  - Toast notifications with auto-dismiss
  - Smooth hover animations and transitions
  - Fully responsive layout

================================================================================
                                TECH STACK
================================================================================

  Layer       | Technology
  ------------|---------------------------
  Backend     | Python, Flask 3.0.0
  Database    | SQLite + Flask-SQLAlchemy
  Frontend    | HTML, CSS, JavaScript
  Auth        | Flask-Login, Werkzeug
  Font        | Google Fonts (Inter)
  Deployment  | Gunicorn, Railway

================================================================================
                             PROJECT STRUCTURE
================================================================================

  ethara/
  |
  |-- app.py                  Main app factory, error handlers, auto-migration
  |-- extensions.py           SQLAlchemy & LoginManager initialization
  |-- models.py               User, Project, Task data models
  |-- requirements.txt        Python dependencies
  |-- pyproject.toml          Build system configuration
  |-- Procfile                Gunicorn process file (deployment)
  |-- railway.json            Railway deployment config
  |
  |-- routes/
  |   |-- __init__.py         Routes package init
  |   |-- auth.py             Login, signup, logout
  |   |-- dashboard.py        Dashboard stats & charts
  |   |-- projects.py         Project CRUD operations
  |   |-- tasks.py            Task CRUD & status updates
  |   |-- settings.py         Profile, security, notifications
  |   +-- team.py             Team management
  |
  |-- templates/
  |   |-- base.html           Layout with navbar & toast system
  |   |-- login.html          Login page
  |   |-- signup.html         Signup page
  |   |-- dashboard.html      Dashboard with stats & charts
  |   |-- projects.html       Projects listing
  |   |-- view_project.html   Single project detail view
  |   |-- create_project.html Project creation form
  |   |-- tasks.html          Tasks listing
  |   |-- create_task.html    Task creation form
  |   |-- team.html           Team members page
  |   +-- settings.html       Settings page
  |
  +-- static/
      |-- style.css           All application styles
      +-- app.js              Toast & animation logic

================================================================================
                            SETUP INSTRUCTIONS
================================================================================

1. CLONE THE REPOSITORY

     git clone https://github.com/harshkr04/Team-Tracker.git
     cd Team-Tracker

2. CREATE A VIRTUAL ENVIRONMENT (recommended)

     python -m venv venv

     Windows  :  venv\Scripts\activate
     Mac/Linux:  source venv/bin/activate

3. INSTALL DEPENDENCIES

     pip install -r requirements.txt

4. RUN THE APPLICATION

     python app.py

5. OPEN IN BROWSER

     http://127.0.0.1:5000

================================================================================
                            DEFAULT ADMIN ACCOUNT
================================================================================

  A default admin account is created automatically on first run:

     Email    : admin@teamtracker.com
     Password : admin123

  ** Change these credentials immediately after first login. **

================================================================================
                              DEPENDENCIES
================================================================================

  Flask              3.0.0
  Flask-SQLAlchemy   3.1.1
  Flask-Login        0.6.3
  Werkzeug           3.0.1
  gunicorn           21.2.0

================================================================================
                            DATA MODELS
================================================================================

  USER
    - id, username, email, password_hash
    - role (admin / member)
    - created_at, last_active
    - notify_email, notify_tasks (notification preferences)

  PROJECT
    - id, name, description
    - created_at, created_by
    - members (many-to-many with User)
    - tasks (one-to-many with Task)

  TASK
    - id, title, description
    - status (pending / in_progress / completed)
    - priority (low / medium / high)
    - due_date, created_at
    - project_id, assigned_to

================================================================================
                           AUTO-MIGRATION
================================================================================

  The application includes a lightweight auto-migration system that
  automatically detects and adds missing columns when the app starts.
  This ensures backward compatibility when the schema evolves without
  requiring manual database migrations.

  Migrations handled:
    - Task table  : priority column
    - User table  : last_active, notify_email, notify_tasks columns
    - Status fix  : Converts old "todo" -> "pending", "done" -> "completed"

================================================================================

  Built with Flask | Ethara.ai

================================================================================
