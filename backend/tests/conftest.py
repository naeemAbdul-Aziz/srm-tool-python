import os
import sys
import pathlib
import pytest
from fastapi.testclient import TestClient

# Ensure project root (one level up from 'backend') is on sys.path so 'backend' package imports work when running from subdirectories
ROOT_DIR = pathlib.Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT_DIR / 'backend'
for p in (str(BACKEND_DIR), str(ROOT_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from backend import api as api_module

# NOTE: These tests assume a test database URL is provided via env var TEST_DATABASE_URL.
# If not set, they will SKIP to avoid polluting production data.

TEST_DB_ENV = 'TEST_DATABASE_URL'

@pytest.fixture(scope='session')
def test_db_url():
    url = os.getenv(TEST_DB_ENV)
    if not url:
        pytest.skip(f"Environment variable {TEST_DB_ENV} not set; skipping DB-dependent tests")
    return url

@pytest.fixture(scope='session', autouse=True)
def configure_test_db(test_db_url, monkeypatch):
    # Force the app to use the test DB
    monkeypatch.setenv('DATABASE_URL', test_db_url)

@pytest.fixture(scope='session')
def client():
    return TestClient(api_module.app)

@pytest.fixture
def ensure_admin_user(client):
    # Create an admin user if not exists directly via DB or signup endpoint (if exists)
    # For now, assume default admin credentials admin:admin123 exist in seed or preloaded.
    # If authentication flow changes, adjust helper here.
    return {'username': 'admin', 'password': 'admin123'}

@pytest.fixture
def basic_auth_header(ensure_admin_user):
    import base64
    token = base64.b64encode(f"{ensure_admin_user['username']}:{ensure_admin_user['password']}".encode()).decode()
    return { 'Authorization': f'Basic {token}' }

# --- Baseline deterministic seed (students, courses, semester, grades) ---
# Ensures tests have a known student 'STUD001' with at least one grade and an admin user.
# Idempotent: uses ON CONFLICT DO NOTHING and existence checks.
@pytest.fixture(scope='session', autouse=True)
def baseline_seed(test_db_url):
    from datetime import date
    import psycopg2
    try:
        from db import (
            connect_to_db, create_tables_if_not_exist,
            insert_student_profile, insert_course, insert_semester, insert_grade,
            fetch_student_by_index_number, fetch_course_by_code, fetch_semester_by_name
        )
        # Direct SQL for users to avoid opening multiple connections in auth.create_user
        conn = connect_to_db()
        if conn is None:
            pytest.skip("Could not connect to test database for seeding")
        create_tables_if_not_exist(conn)

        with conn.cursor() as cur:
            # Admin user
            cur.execute("""
                INSERT INTO users (username, password, role)
                VALUES ('admin', '$2b$12$3qOHvXoO5nTr0y1Q0z/QCud2AV/QXpVZl8vGeOawx2UY8ailqXFyW', 'admin')
                ON CONFLICT (username) DO NOTHING;
            """)  # bcrypt hash for 'admin123' (do not change without updating tests)
            # Student user (username == index number)
            cur.execute("""
                INSERT INTO users (username, password, role)
                VALUES ('STUD001', '$2b$12$3qOHvXoO5nTr0y1Q0z/QCud2AV/QXpVZl8vGeOawx2UY8ailqXFyW', 'student')
                ON CONFLICT (username) DO NOTHING;
            """)
            conn.commit()

        # Ensure minimal semester
        semester = fetch_semester_by_name(conn, 'Semester 1')
        if not semester:
            semester_id = insert_semester(conn, 'Semester 1', date(2024,1,1), date(2024,6,30), academic_year='2024/2025')
        else:
            semester_id = semester['semester_id']

        # Ensure minimal course
        course = fetch_course_by_code(conn, 'TEST101')
        if not course:
            course_id = insert_course(conn, 'TEST101', 'Test Foundations', 3)
        else:
            course_id = course['course_id']

        # Ensure student profile
        student_profile = fetch_student_by_index_number(conn, 'STUD001')
        if not student_profile:
            student_id = insert_student_profile(
                conn,
                'STUD001', 'Baseline Student', date(2004,1,1), 'M',
                'baseline@student.test', None, 'Computer Science', 1
            )
        else:
            student_id = student_profile['student_id']

        # Insert a grade if none exists for this (student, course, semester)
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 1 FROM grades g
                JOIN courses c ON g.course_id=c.course_id
                JOIN semesters s ON g.semester_id=s.semester_id
                WHERE g.student_id=%s AND c.course_code=%s AND s.semester_name=%s;
            """, (student_id, 'TEST101', 'Semester 1'))
            exists = cur.fetchone()
        if not exists:
            # Simple deterministic score/grade
            from grade_util import calculate_grade, get_grade_point
            score = 85.0
            grade = calculate_grade(score)
            gp = get_grade_point(grade)
            insert_grade(conn, student_id, course_id, semester_id, score, grade, gp, '2024/2025')

        conn.close()
        return {
            'student_index': 'STUD001',
            'course_code': 'TEST101',
            'semester_name': 'Semester 1'
        }
    except psycopg2.OperationalError:
        pytest.skip("OperationalError during baseline seeding; skipping DB-dependent tests")
    except Exception as e:
        pytest.fail(f"Baseline seed failed: {e}")
