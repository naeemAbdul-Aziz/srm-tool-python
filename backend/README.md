# Student Result Management System (SRMS) – Backend

Robust academic records and reporting backend built with FastAPI, PostgreSQL, and Python. Provides APIs, CLI tools, notification delivery (with real‑time Server‑Sent Events), comprehensive report generation (TXT / CSV / Excel / PDF), and deterministic seeding utilities.

## ✨ Key Features

- Dual interfaces: FastAPI REST API & interactive CLI (`main.py` / `menu.py`).
- Student & course management with semesters and grades.
- GPA & grade utilities (deterministic mapping A–F).
- Reports:
  - Summary reports: TXT, CSV, Excel, PDF.
  - Personal academic report (per student) PDF / TXT.
  - Academic transcript: Excel & PDF (official format) with corrected GPA logic.
- Notification system:
  - Admin publishing, unread tracking, pagination (cursor via `before_id`).
  - Real‑time streaming via Server‑Sent Events (`/notifications/stream`).
  - Fallback friendly to polling.
- Seeding:
  - Baseline deterministic seed for tests (fixtures).
  - Comprehensive realistic dataset (`comprehensive_seed.py`).
  - Modular constants (`seed_constants.py`) & idempotent helpers (`seed_helpers.py`).
- Authentication: HTTP Basic (bcrypt hashed passwords) + session tracking.
- Export resilience: in‑memory generation with correct headers (Excel/CSV/PDF) tested.
- Test suite (pytest) covering exports, notifications, transcripts.
- Optimized UX: unified global loading spinner (eliminated duplicate overlay) with reference-counted show/hide logic.
- Simplified role model: only `admin` and `student` (legacy registrar/dean optional via env var).

## 🧱 Architecture Overview

```
backend/
├── api.py                # FastAPI application (reports, notifications, students, grades)
├── main.py               # CLI entry point
├── menu.py               # CLI interactive menu
├── auth.py               # Basic auth + password hashing
├── db.py                 # DB connection helpers & query utilities
├── course_management.py  # Course & semester operations
├── grade_util.py         # Grade & GPA utilities
├── report_utils.py       # All report & transcript export logic
├── comprehensive_seed.py # Comprehensive dataset seeding orchestrator
├── seed_constants.py     # Static datasets (names, courses, calendar fragments)
├── seed_helpers.py       # Idempotent ensure_* helpers & generation logic
├── bulk_importer.py      # CSV import routines
├── session.py            # Session/user context management
├── logger.py             # Structured logging setup
├── tests/                # pytest test suite
└── requirements.txt      # Dependencies
```

## 🔐 Authentication

The system uses HTTP Basic Auth (no JWT). Passwords are stored hashed (bcrypt).

 Roles:
 - `admin` – full access (management, reports, notifications, seeding, instructor assignment)
 - `instructor` – limited management: view assigned courses, add/list/delete materials for those courses, enter/update grades, view notifications
 - `student` – personal profile, grades, personal reports

Seeded credentials (comprehensive seed):
```
Admin: admin / admin123
Students: password = last 4 digits of index_number + "2024"
Example: index ug10127 -> password 01272024
```

Optional legacy demo admins (registrar / dean) can be added by setting `SEED_EXTRA_ADMINS=true` before running `comprehensive_seed.py`. They use:
```
registrar / registrar123
dean      / dean123
```
All admin-like accounts share the same `admin` role value.

 Instructor accounts – now REALISTIC BY DEFAULT:

 • By default the seeder generates realistic instructors unless you pass `--no-instructors` or set `SEED_REALISTIC_INSTRUCTORS=false`.
 • Control count via `--instructors N` or env `SEED_INSTRUCTORS_COUNT` (fallback = 15 default now).
 • Each instructor gets: Ghanaian full name, academic title (Prof./Dr./Mr./Ms./Mrs.), school, program, specialization, contact info & office.
 • Usernames follow `firstname.lastname` with numeric suffix collision handling; password = `<username>123` (demo only!).
 • Course Coverage Guarantee: Every course is assigned at least one instructor (primary round‑robin). Up to two additional random instructors may be associated for richer analytics.
 • Legacy simple demo accounts (`instructor1 / instructor123`) are only created if you explicitly set `SEED_REALISTIC_INSTRUCTORS=false` AND omit `--no-instructors`.

 Disable all instructor creation entirely with `--no-instructors`.

Assignments can then be created via API (see endpoints below) or automatically by the realistic seeder.

## 🧮 Grading & GPA

Current grade scale (as implemented in `grade_util.py`):

| Score | Grade | Points (4.0 scale) |
|-------|-------|-------------------|
| 80–100 | A | 4.0 |
| 70–79  | B | 3.0 |
| 60–69  | C | 2.0 |
| 50–59  | D | 1.0 |
| 0–49   | F | 0.0 |

GPA formula: `Σ(grade_point * credit_hours) / Σ(credit_hours)`.

Transcript exports (Excel + PDF) now use `get_grade_point(score)` directly (previous misuse of `calculate_gpa([score])` removed).

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- PostgreSQL 12+
- (Optional) Git

### 1. Clone & Environment
```bash
git clone https://github.com/naeemAbdul-Aziz/srm-tool-python.git
cd srm-tool-python/backend
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Database
Create PostgreSQL database (adapt user/password as needed):
```bash
createdb srms-db
```
Create a `.env` file:
```env
DB_NAME=srms-db
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
APP_DEBUG=True
LOG_LEVEL=INFO
SECRET_KEY=change_me_in_production
SESSION_TIMEOUT=3600
```

### 3. Initialize
CLI (interactive):
```bash
python main.py
```
API server (dev):
```bash
uvicorn api:app --reload
```
Visit: http://localhost:8000/docs

### 4. Seed Data
Comprehensive dataset:
```bash
python comprehensive_seed.py
```
Test baseline seeding occurs automatically in pytest fixtures (for deterministic tests).

## 📡 Notifications System

Endpoints (admin create, user consumption):
- `GET /notifications` – list (supports pagination with `before_id`)
- `POST /notifications` – create (admin)
- `POST /notifications/{id}/read` – mark one read
- `POST /notifications/read-all` – mark all read
- `GET /notifications/stream` – SSE real‑time stream

Client can open an `EventSource` to receive push notifications; fallback polling still works.

## 🧪 Assessments API
Track structured evaluation components (e.g., Quiz, Midterm, Final) with weights for future weighted grade aggregation.

Endpoints:
- `GET /assessments` – list all assessments (optionally filter by `course_code`)
- `POST /assessments` (admin) – create or upsert assessment
- `PUT /assessments/{assessment_id}` (admin) – update name / max_score / weight
- `DELETE /assessments/{assessment_id}` (admin) – remove assessment

Sample create payload:
```json
{
  "course_code": "UGCS101",
  "assessment_name": "Quiz 1",
  "max_score": 20,
  "weight": 10
}
```

Notes:
- `weight` is a percentage placeholder; aggregation into final grades pending a future phase.
- Idempotent create via (course_code, assessment_name) uniqueness enforced by upsert logic.

## 📑 Reports & Transcripts

Summary reports (multi-format, Excel multi-sheet):
`GET /admin/reports/summary?format=txt|csv|excel|pdf`

Personal academic report (admin – any student):
`GET /admin/reports/personal/{student_index}?format=txt|pdf`

Personal academic report (student self-service):
`GET /student/report/pdf` and `GET /student/report/txt`

Transcript (official academic record):
`GET /admin/reports/transcript/{student_index}?format=excel|pdf`

Reliability features: size validation, unified headers (`Content-Disposition`, `Content-Length`), temporary file cleanup, deterministic seeding for test fixtures. Automated coverage in `tests/test_exports.py`.

## 📚 Course Materials & Instructor Workflows

New instructor-focused endpoints enable distributing per-course reference material links and delegated grade entry.

Endpoints:
```
POST /courses/{course_id}/instructors            # (admin) assign instructor by username
GET  /courses/{course_id}/instructors            # (admin or assigned instructor)
DELETE /courses/{course_id}/instructors/{user_id}# (admin) remove assignment
GET  /instructors/me/courses                     # (instructor) list own courses
POST /courses/{course_id}/materials              # (admin or assigned instructor) add material
GET  /courses/{course_id}/materials              # (admin or assigned instructor)
DELETE /courses/{course_id}/materials/{material_id}
POST /instructor/grades                          # (admin or assigned instructor) grade entry using course_code + student_index
```

### Instructor Analytics Endpoints (New)
Provide role-scoped performance and engagement insight. All require Basic Auth. Instructors are limited to their own assigned courses; admins bypass mapping checks.

```
GET  /instructors/me/overview                               # Aggregated overview (course list, student counts, avg score, pass rate, grade distributions)
GET  /instructors/me/courses/{course_id}/performance         # Per-course stats (avg, median, pass rate, grade distribution, top/bottom N students)
GET  /instructors/me/courses/{course_id}/students            # Roster (index_number, full_name, score, grade)
```

Sample /instructors/me/overview response (abridged):
```json
{
  "courses": [
    {
      "course_id": 12,
      "course_code": "UGCS201",
      "course_title": "Data Structures",
      "student_count": 48,
      "avg_score": 73.54,
      "pass_rate": 0.8958,
      "grade_distribution": {"A": 9, "B": 18, "C": 15, "D": 1, "F": 5}
    }
  ],
  "totals": {"course_count": 3, "distinct_students": 120}
}
```

Performance endpoint example:
```json
{
  "course": {"course_id": 12, "course_code": "UGCS201", "course_title": "Data Structures"},
  "avg_score": 73.54,
  "median_score": 74.0,
  "pass_rate": 0.8958,
  "grade_distribution": {"A": 9, "B": 18, "C": 15, "D": 1, "F": 5},
  "top_students": [{"score": 95.0, "grade": "A", "index_number": "ug10123", "full_name": "Ama Mensah"}],
  "bottom_students": [{"score": 42.0, "grade": "F", "index_number": "ug10077", "full_name": "Yaw Asare"}]
}
```

Error Cases:
- 403 if instructor attempts performance/students endpoint for an unassigned course.
- 404 if course not found or no data (performance endpoint).

Use Cases:
- Instructor dashboards (course load, at-risk detection).
- Admin supervision & quality assurance.
- Future extension: caching, trend deltas, anonymized benchmarking.

Authorization Logic Highlights:
- Material and grade entry checks confirm instructor-course assignment via `course_instructors` mapping.
- Admin bypasses course assignment checks.
- Students currently cannot view materials (policy placeholder; can be extended later).

Frontend Enhancements:
- Solid-color design tokens (`:root` CSS variables) providing neutral palette.
- Instructor dashboard panel (course list with inline materials management & grade entry form).
- Admin instructor management panel (assign/remove instructors, real-time list refresh).

Testing Additions:
- `tests/test_instructors.py` exercises assignment, materials CRUD, and grade entry permissions.


## 🧪 Testing

Run all tests:
```bash
pytest -q
```

Exports & transcript tests rely on the deterministic seed fixture creating `STUD001` with at least one course & grade.
Instructor & materials tests rely on seeded or dynamically created instructor users; seeding helper can populate `instructor1`.

## 🧬 Seeding Modes

| Mode | Description |
|------|-------------|
| Baseline | Fast minimal dataset (≤10 students, 1 admin set, core semesters, few or no grades) |
| Comprehensive | Standard full dataset (default): distributed students, all courses & semesters, full grade generation |
| Exhaustive | Comprehensive + assessments, program coverage enforcement, partial students, curated GPA edge cases, notifications, current semester, read/unread state |

Refactor highlights:
- Constants extracted to `seed_constants.py`.
- Idempotent ensure/create helpers in `seed_helpers.py`.
- Reduced duplication in `comprehensive_seed.py`.
### Deterministic & Silent Seeding

The comprehensive seeder supports reproducible runs and optional notification suppression.

Environment variables:

| Variable | Purpose | Example |
|----------|---------|---------|
| `SEED_RANDOM_SEED` | Default deterministic seed (overridden by `--seed`) | `SEED_RANDOM_SEED=12345` |
| `SUPPRESS_SEED_NOTIFICATIONS` | Skip creating notifications during seeding | `SUPPRESS_SEED_NOTIFICATIONS=1` |
| `SEED_REALISTIC_INSTRUCTORS` | (Default ON) Realistic instructor generation (`false` to fall back to legacy) | `SEED_REALISTIC_INSTRUCTORS=false` |
| `SEED_INSTRUCTORS_COUNT` | Number of instructors if CLI flag absent | `SEED_INSTRUCTORS_COUNT=8` |

CLI flags (view all with `python comprehensive_seed.py --help`):

| Flag | Description |
|------|-------------|
| `--num-students N` | Number of students (default 100) |
| `--no-clean` | Do not wipe existing data first |
| `--seed SEED` | Deterministic seed (int or string) |
| `--suppress-notifications` | Suppress notifications (also via env) |
| `--baseline` | Use baseline mode (minimal quick seed) |
| `--exhaustive` | Enable exhaustive mode features |
| `--assessments-sample N` | Limit number of courses for which assessments are created |
| `--instructors N` | Override default count of realistic instructors |
| `--no-instructors` | Skip instructor creation entirely |
| `--full-reset` | Wipe all data including admin users & notifications before seeding |
| `-y / --yes` | Auto-confirm (non-interactive) |

Examples:

Deterministic (seed via env):
```bash
SEED_RANDOM_SEED=42 python comprehensive_seed.py -y
```

Explicit seed overrides env:
```bash
python comprehensive_seed.py --seed 9999 -y
```

Silent bulk run:
```bash
python comprehensive_seed.py --num-students 250 --suppress-notifications -y
```

Programmatic API:
```python
from comprehensive_seed import seed_comprehensive_database
seed_comprehensive_database(num_students=50, random_seed=123, suppress_notifications=True)
```

Precedence: CLI `--seed` > env `SEED_RANDOM_SEED` > nondeterministic.

Suppression is enforced within `db.insert_notification` (guarding all higher-level creators).

## 🧾 Logging
Logs go to `app.log` plus console. Configure via `LOG_LEVEL` env var. Use DEBUG for detailed seeding diagnostics.

## 🔧 Troubleshooting (Quick)

| Symptom | Fix |
|---------|-----|
| Cannot connect DB | Verify `.env`, ensure PostgreSQL running, test with `psql` |
| Auth fails | Confirm Basic Auth header (browser or API client) & seeded credentials |
| Empty reports | Ensure grades exist; run seeding script |
| SSE not receiving | Check browser console & ensure endpoint `/notifications/stream` reachable |
| GPA seems off | Confirm credit hours present and transcript regenerated (post-fix) |

## 🗺️ Roadmap
- Extended PDF styling & optional watermarking.
- Analytics / assessment expansion (more derived metrics & dashboards).
- Additional test coverage: notification suppression & deterministic integrity snapshot.
- Optional user-facing feature flags (AppConfig style) for experimental exports.

## 📄 License
See `LICENSE` file.

## 🙋 Support
Open an issue or inspect `app.log` for detailed tracebacks. Contributions and refinements welcome.

---
This README reflects current feature set (notifications SSE, transcript PDF/Excel parity, GPA fix, seeding refactor) and removes outdated JWT / duplicated sections.

```
backend/
├── APPLICATION ENTRY POINTS
│   ├── main.py                    # CLI application launcher
│   ├── api.py                     # FastAPI server (22+ endpoints)
│   └── menu.py                    # Interactive CLI menu system
│
├── CORE SYSTEM MODULES  
│   ├── db.py                      # Database operations & UG schema
│   ├── auth.py                    # Authentication & authorization cloning the repository)
- A text editor or IDEd CLI application for managing student records, grades, and academic reports. Built with FastAPI, PostgreSQL, and Python.

## Overview

The Student Result Management System (SRMS) backend provides a robust platform for educational institutions to manage student data, academic records, and generate comprehensive reports. The system supports both REST API and command-line interfaces for maximum flexibility.

### Key Features

- **Dual Interface**: REST API (FastAPI) and CLI application support
- **Comprehensive Student Management**: Profile creation, updates, and academic tracking
- **Grade Management**: Course enrollment, grade recording, and GPA calculations
- **Authentication & Authorization**: Role-based access control (Admin/Student)
- **Bulk Import/Export**: CSV file support for mass data operations
- **Report Generation**: PDF and TXT academic reports
- **University of Ghana Integration**: Pre-configured with authentic UG academic structure
- **Production Ready**: Comprehensive error handling, logging, and validation

## Architecture

### Core Components

```
backend/
├── api.py                    # FastAPI REST API endpoints
├── main.py                   # CLI application entry point
├── menu.py                   # Interactive CLI menu system
├── db.py                     # Database operations and models
├── auth.py                   # Authentication and user management
├── config.py                 # Configuration and environment variables
├── grade_util.py             # Grade calculations and utilities
├── course_management.py      # Academic course and semester management
├── bulk_importer.py          # CSV bulk import functionality
├── report_utils.py           # PDF/TXT report generation
├── session.py                # Session management
├── logger.py                 # Centralized logging system
├── file_handler.py           # File operations and validation
└── comprehensive_seed.py     # Database seeding with realistic data
```

### Database Schema

- **users**: Authentication credentials and user roles
- **student_profiles**: Student personal and academic information  
- **courses**: Academic course catalog with codes and credits
- **semesters**: Academic periods and scheduling
- **grades**: Student performance records and calculations
- **assessments**: Individual assignment and exam tracking

### Student Features  
- **Profile Management**: View/update personal information
- **Grade Viewing**: Semester grades, cumulative records
- **GPA Calculations**: Semester and cumulative GPA
- **Transcript Access**: Complete academic history
- **Course Information**: Enrolled courses, credit hours

### University of Ghana Integration
- **7 Schools/Colleges**: All major UG academic units
- **50+ Programs**: Authentic degree programs
- **130+ Courses**: Real UG course codes and titles
- **Academic Calendar**: Proper semester/academic year format
- **Grading System**: UG-compliant grading scale
- **Student Records**: UG index format (ug#####)
- **Contact Systems**: UG email formats (@st.ug.edu.gh)

## � Quick Start Guide

This guide will get you up and running with the Student Result Management System in under 10 minutes.

### Prerequisites Check
Before starting, ensure you have:
- Python 3.9 or higher (`python --version`)
- PostgreSQL 12 or higher (`psql --version`)
- Git (for cloning the repository)
- A text editor or IDE

### Step 1: Project Setup

```bash
# Clone the repository
git clone https://github.com/naeemAbdul-Aziz/srm-tool-python.git
cd srm-tool-python/backend

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install all dependencies
pip install -r requirements.txt
```

### Step 2: Database Setup

```bash
# Create PostgreSQL database
createdb srms-db

# If you need to create a PostgreSQL user:
# psql -c "CREATE USER srms_user WITH PASSWORD 'your_password';"
# psql -c "GRANT ALL PRIVILEGES ON DATABASE srms-db TO srms_user;"
```

### Step 3: Environment Configuration

Create a `.env` file in the backend directory:

```bash
# Create .env file
cat > .env << EOF
# Database Configuration
DB_NAME=srms-db
DB_USER=postgres
DB_PASSWORD=your_database_password
DB_HOST=localhost
DB_PORT=5432

# Application Configuration
APP_DEBUG=True
LOG_LEVEL=INFO
SECRET_KEY=your-super-secret-key-change-in-production
SESSION_TIMEOUT=3600
EOF
```

**Important**: Replace `your_database_password` with your actual PostgreSQL password!

### Step 4: Initialize the System

Choose one of these initialization methods:

#### Option A: CLI Initialization (Recommended for beginners)
```bash
# Start the CLI application
python main.py

# Follow the interactive setup:
# 1. The system will create database tables automatically
# 2. Choose "Sign Up" to create your first admin account
# 3. Select "Admin" role
# 4. Create username/password (remember these!)
```

#### Option B: API Initialization (For developers)
```bash
# Start the API server in background
python -c "
import subprocess
import time
proc = subprocess.Popen(['python', 'api.py'])
time.sleep(3)  # Wait for server to start
print('API server started on http://localhost:8000')
"

# Initialize via API
curl -X POST "http://localhost:8000/initialize"
```

### Step 5: Load Sample Data (Optional but Recommended)

```bash
# Generate comprehensive University of Ghana sample data
python comprehensive_seed.py

# This creates:
# - 100 realistic student profiles with Ghanaian names
# - 130+ authentic UG courses across all schools
# - 8 semesters (2021/2022 through 2024/2025)
# - Realistic grade distributions
# - Complete user accounts for all students
```

### Step 6: Test Your Installation

#### Test CLI Interface:
```bash
python main.py

# Login with your admin credentials
# Try: Admin Menu → View all student records
```

#### Test API Interface:
```bash
# Start API server
python api.py

# In another terminal, test the API:
curl http://localhost:8000/health

# Access interactive documentation:
# Open browser: http://localhost:8000/docs
```

### Step 7: Verify Everything Works

Run these verification commands:

```bash
# Test database connection
python -c "from db import connect_to_db; print('Database OK' if connect_to_db() else 'Database Error')"

# Test API endpoints
curl -s http://localhost:8000/ | grep -q "Student Result Management" && echo "API OK" || echo "API Error"

# Check if sample data loaded
python -c "
from db import connect_to_db
conn = connect_to_db()
if conn:
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM student_profiles')
    count = cur.fetchone()[0]
    print(f'{count} students loaded' if count > 0 else 'No sample data')
    conn.close()
"
```

## What You Can Do Now

### As Administrator:
1. **Manage Students**: Add, update, search, and bulk import students
2. **Manage Courses**: Create courses and academic semesters  
3. **Manage Grades**: Enter grades and generate transcripts
4. **View Analytics**: Student performance and grade distributions
5. **Generate Reports**: PDF and TXT academic reports

### As Student (using sample data):
1. **Login Credentials**: Index number + password (e.g., `ug10001` / `00012024`)
2. **View Profile**: Personal academic information
3. **Check Grades**: Semester grades and cumulative GPA
4. **Academic History**: Complete grade records

### API Integration:
- **Documentation**: Visit `http://localhost:8000/docs`
- **Health Check**: `GET http://localhost:8000/health`
- **Student Data**: `GET http://localhost:8000/admin/students` (with auth)

## Default Accounts (After Sample Data)

### Admin Accounts:
```
Username: admin
Password: admin123
Role: Administrator
```

### Sample Student Accounts:
```
Index: ug10001 | Password: 00012024 | Name: Kwame Asante
Index: ug10002 | Password: 00022024 | Name: Ama Mensah  
Index: ug10003 | Password: 00032024 | Name: Kofi Osei
...and 97 more students
```

Password pattern: `[last 4 digits of index]2024`

## Common Startup Issues & Solutions

### Issue: "Module not found" errors
```bash
# Solution: Ensure virtual environment is activated
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Issue: Database connection failed
```bash
# Solution: Check PostgreSQL service and credentials
sudo systemctl start postgresql  # Linux
brew services start postgresql   # macOS
# Windows: Start PostgreSQL service via Services

# Test connection manually:
psql -d srms-db -U postgres
```

### Issue: Permission denied on database
```bash
# Solution: Grant proper permissions
psql -c "GRANT ALL PRIVILEGES ON DATABASE \"srms-db\" TO postgres;"
```

### Issue: API server won't start
```bash
# Solution: Check if port 8000 is available
netstat -an | grep 8000

# Kill existing process if needed:
pkill -f "python api.py"

# Try different port:
uvicorn api:app --port 8001
```

### Issue: No sample data appears
```bash
# Solution: Run seeding script manually
python comprehensive_seed.py

# Check if data was created:
python -c "
from db import connect_to_db
conn = connect_to_db()
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM student_profiles')
print(f'Students: {cur.fetchone()[0]}')
cur.execute('SELECT COUNT(*) FROM courses')  
print(f'Courses: {cur.fetchone()[0]}')
conn.close()
"
```

## You're Ready!

Congratulations! You now have a fully functional Student Result Management System. Here's what to explore next:

1. **Try the CLI**: `python main.py` - Full administrative interface
2. **Explore the API**: `http://localhost:8000/docs` - Interactive documentation
3. **Check the logs**: `tail -f app.log` - Monitor system activity
4. **Read the docs**: Continue reading this README for advanced features

### Next Steps:
- Read the full [API Documentation](#api-endpoints)
- Explore [Configuration Options](#configuration)
- Learn about [Production Deployment](#production-deployment)
- Run the [Test Suite](#testing)

**Need Help?** Check the [Troubleshooting](#troubleshooting) section or review the logs in `app.log`.

## �📁 Project Architecture

```
backend/
├── 🚀 APPLICATION ENTRY POINTS
│   ├── main.py                    # CLI application launcher
│   ├── api.py                     # FastAPI server (22+ endpoints)
│   └── menu.py                    # Interactive CLI menu system
│
├── 🏛️ CORE SYSTEM MODULES  
│   ├── db.py                      # Database operations & UG schema
│   ├── auth.py                    # Authentication & authorization
## Installation & Setup

### Prerequisites

- Python 3.9+
- PostgreSQL 12+
- Virtual environment (recommended)

### 1. Environment Setup

```bash
# Clone and navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Configuration

Create a `.env` file in the backend directory:

```env
# Database Configuration
DB_NAME=srms-db
DB_USER=postgres
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=5432

# Application Configuration
APP_DEBUG=False
LOG_LEVEL=INFO
SECRET_KEY=your_super_secret_key_here
SESSION_TIMEOUT=3600
```

### 3. Database Setup

```bash
# Create PostgreSQL database
createdb srms-db

# Initialize database tables (automatic on first run)
python main.py
```

### 4. Seed Sample Data (Optional)

```bash
# Generate comprehensive University of Ghana sample data
python comprehensive_seed.py
```

## Usage

### REST API Server

Start the FastAPI development server:

```bash
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

API Documentation available at:
- Interactive docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### CLI Application

Run the interactive command-line interface:

```bash
python main.py
```

## API Endpoints

### Authentication
- `GET /me` - Get current user information
- `POST /admin/users` - Create new user account

### System Management
- `GET /` - API status and information
- `GET /health` - System health check
- `POST /initialize` - Initialize database tables
- `POST /admin/seed-comprehensive` - Generate sample data

### Student Management
- `POST /admin/students` - Create student profile
- `GET /admin/students` - List all students (paginated)
- `GET /admin/students/search` - Search students by criteria
- `GET /admin/students/{index_number}` - Get specific student
- `PUT /admin/students/{index_number}` - Update student profile
- `POST /admin/students/bulk` - Bulk import students from CSV

### Academic Management
- `POST /admin/courses` - Create new course
- `GET /admin/courses` - List all courses
- `POST /admin/semesters` - Create new semester
- `GET /admin/semesters` - List all semesters

### Grade Management
- `POST /admin/grades` - Record student grade
- `GET /admin/grades` - List grades with filtering
- `GET /student/grades` - Get student's own grades
- `GET /student/gpa` - Calculate student GPA

### Student Portal
- `GET /student/profile` - Get student profile
- `GET /student/grades` - View personal grades
- `GET /student/gpa` - View calculated GPA

### Reports & Analytics
- `GET /admin/students/analytics` - Student performance analytics
- `GET /admin/grades/analytics` - Grade distribution analytics
- `POST /admin/reports/export` - Generate and export reports

## Authentication

The system uses HTTP Basic Authentication with role-based access control:

### Admin Access
- Username: admin credentials
- Full system access including user management, bulk operations, and analytics

### Student Access  
- Username: student index number (e.g., `ug12345`)
- Access limited to personal profile and grades

### Default Credentials (Seeded Data)
- Admin: `admin` / `admin123`
- Students: `{index_number}` / `{last_4_digits}2024`

## Data Models

### Student Profile
```json
{
  "index_number": "ug12345",
  "full_name": "John Doe",
  "dob": "2000-01-15",
  "gender": "Male",
  "contact_email": "john.doe@ug.edu.gh",
  "phone": "+233123456789",
  "program": "Computer Science",
  "year_of_study": 2
}
```

### Course
```json
{
  "course_code": "CSCI201",
  "course_title": "Data Structures and Algorithms",
  "credit_hours": 3
}
```

### Grade Record
```json
{
  "student_id": 1,
  "course_id": 1,
  "semester_id": 1,
  "score": 85.5,
  "grade": "B+",
  "grade_point": 3.5,
  "academic_year": "2024/2025"
}
```

## Bulk Import Format

CSV files for bulk student import should follow this structure:

```csv
index_number,full_name,dob,gender,contact_email,program,year_of_study
ug12345,John Doe,2000-01-15,Male,john@ug.edu.gh,Computer Science,2
ug12346,Jane Smith,1999-12-03,Female,jane@ug.edu.gh,Mathematics,3
```

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DB_NAME` | PostgreSQL database name | `srms-db` | No |
| `DB_USER` | Database username | `postgres` | No |
| `DB_PASSWORD` | Database password | - | **Yes** |
| `DB_HOST` | Database host | `localhost` | No |
| `DB_PORT` | Database port | `5432` | No |
| `SECRET_KEY` | Application secret key | - | **Yes** |
| `SESSION_TIMEOUT` | Session timeout (seconds) | `3600` | No |
| `LOG_LEVEL` | Logging level | `INFO` | No |
| `APP_DEBUG` | Debug mode | `False` | No |

### Logging

The system uses structured logging with different levels:
- `DEBUG`: Detailed diagnostic information
- `INFO`: General application flow
- `WARNING`: Unexpected situations that don't stop execution
- `ERROR`: Serious problems that may prevent functionality

Logs are written to `app.log` and console output.

## Grade Calculation

### University of Ghana Grading Scale

| Score Range | Letter Grade | Grade Point |
|-------------|--------------|-------------|
| 80-100 | A | 4.0 |
| 75-79 | B+ | 3.5 |
| 70-74 | B | 3.0 |
| 65-69 | C+ | 2.5 |
| 60-64 | C | 2.0 |
| 55-59 | D+ | 1.5 |
| 50-54 | D | 1.0 |
| 45-49 | E | 0.5 |
| 0-44 | F | 0.0 |

### GPA Calculation
```
GPA = Σ(Grade Point × Credit Hours) / Σ(Credit Hours)
```

## Error Handling

The API provides consistent error responses:

```json
{
  "success": false,
  "message": "Error description",
  "error_code": "VALIDATION_ERROR",
  "details": {
    "field": "Specific validation issue"
  }
}
```

Common HTTP status codes:
- `200`: Success
- `201`: Created
- `400`: Bad Request (validation errors)
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `500`: Internal Server Error

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest test_api.py -v
```

### Test Categories
- **Unit Tests**: Individual function testing
- **Integration Tests**: Database and API endpoint testing
- **Authentication Tests**: Login and permission validation
- **Data Validation Tests**: Input validation and error handling

## Performance Considerations

### Database Optimization
- Indexed columns: `index_number`, `course_code`, `semester_name`
- Connection pooling for concurrent requests
- Prepared statements for security and performance

### API Performance
- Pagination for large result sets (default: 50 items per page)
- Query optimization with selective field loading
- Response caching for static data (courses, semesters)

### Scalability
- Stateless design for horizontal scaling
- Async operations for non-blocking I/O
- Configurable session management

## Security Features

### Data Protection
- Password hashing with bcrypt
- SQL injection prevention with parameterized queries
- Input validation with Pydantic models
- CORS configuration for cross-origin requests

### Access Control
- Role-based authentication (Admin/Student)
- Session timeout management
- API rate limiting capabilities
- Secure environment variable handling

## Production Deployment

### Recommended Setup
```bash
# Production server
gunicorn api:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# With process manager
systemctl start srms-api
systemctl enable srms-api
```

### Environment Checklist
- [ ] Set strong `SECRET_KEY`
- [ ] Configure secure database credentials
- [ ] Enable HTTPS/SSL
- [ ] Set up database backups
- [ ] Configure log rotation
- [ ] Monitor system resources
- [ ] Set up error alerting

## Troubleshooting

### Common Issues

**Database Connection Errors**
```bash
# Check PostgreSQL service
sudo systemctl status postgresql

# Verify database exists
psql -l | grep srms-db

# Test connection
python -c "from db import connect_to_db; print('OK' if connect_to_db() else 'Failed')"
```

**Import Errors**
```bash
# Install missing dependencies
pip install -r requirements.txt

# Check Python path
python -c "import sys; print(sys.path)"
```

**Permission Issues**
```bash
# Check file permissions
ls -la *.py

# Database user permissions
psql -c "SELECT current_user, session_user;"
```

### Debug Mode
Enable debug mode for detailed error information:
```env
APP_DEBUG=True
LOG_LEVEL=DEBUG
```

## API Integration Examples

### Python Client
```python
import requests

# Authentication
auth = ('admin', 'admin123')

# Create student
student_data = {
    "index_number": "ug12345",
    "full_name": "John Doe",
    "program": "Computer Science"
}
response = requests.post(
    "http://localhost:8000/admin/students",
    json=student_data,
    auth=auth
)
print(response.json())
```

### JavaScript/Node.js
```javascript
const axios = require('axios');

const client = axios.create({
  baseURL: 'http://localhost:8000',
  auth: {
    username: 'admin',
    password: 'admin123'
  }
});

// Get all students
client.get('/admin/students')
  .then(response => console.log(response.data))
  .catch(error => console.error(error.response.data));
```

### cURL Examples
```bash
# Get API status
curl http://localhost:8000/

# Create student (requires authentication)
curl -X POST http://localhost:8000/admin/students \
  -u admin:admin123 \
  -H "Content-Type: application/json" \
  -d '{"index_number":"ug12345","full_name":"John Doe"}'

# Get student grades
curl http://localhost:8000/student/grades \
  -u ug12345:50242024
```

---

**Note**: This system is designed for educational institutions and includes features specific to the University of Ghana academic structure. The codebase can be adapted for other institutions by modifying the course codes, grading scales, and academic calendar configurations in the respective modules.
