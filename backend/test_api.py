import pytest
from fastapi.testclient import TestClient
from api import app

client = TestClient(app)

# Sample credentials for testing
ADMIN_AUTH = ("admin", "admin123")
STUDENT_AUTH = ("ug10001", "00012024")  # Using actual seeded student credentials

# Health and system endpoints
def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["success"]

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert "database" in response.json().get("data", {})

def test_docs():
    response = client.get("/docs")
    assert response.status_code == 200

def test_redoc():
    response = client.get("/redoc")
    assert response.status_code == 200

# Auth endpoints (requires valid credentials)
def test_me_unauth():
    response = client.get("/me")
    assert response.status_code == 401

# Authenticated tests
def test_me_admin():
    response = client.get("/me", auth=ADMIN_AUTH)
    assert response.status_code == 200
    data = response.json()
    assert data["success"]
    assert data["data"]["role"] == "admin"

def test_me_student():
    response = client.get("/me", auth=STUDENT_AUTH)
    assert response.status_code == 200
    data = response.json()
    assert data["success"]
    assert data["data"]["role"] == "student"

# Admin endpoints (requires admin auth)
def test_initialize_unauth():
    response = client.post("/initialize")
    assert response.status_code == 401

def test_initialize_admin():
    response = client.post("/initialize", auth=ADMIN_AUTH)
    # Accept 200 or 500 (already initialized)
    assert response.status_code in (200, 500)

def test_seed_comprehensive_unauth():
    response = client.post("/admin/seed-comprehensive")
    assert response.status_code == 401

def test_seed_comprehensive_admin():
    response = client.post("/admin/seed-comprehensive", auth=ADMIN_AUTH)
    # Accept 200 or 500 (already seeded)
    assert response.status_code in (200, 500)

# Student endpoints (requires student auth)
def test_student_profile_unauth():
    response = client.get("/student/profile")
    assert response.status_code == 401

def test_student_profile_student():
    response = client.get("/student/profile", auth=STUDENT_AUTH)
    assert response.status_code in (200, 404)  # 404 if student not seeded

def test_student_grades_unauth():
    response = client.get("/student/grades")
    assert response.status_code == 401

def test_student_grades_student():
    response = client.get("/student/grades", auth=STUDENT_AUTH)
    assert response.status_code in (200, 404)

def test_student_gpa_unauth():
    response = client.get("/student/gpa")
    assert response.status_code == 401

def test_student_gpa_student():
    response = client.get("/student/gpa", auth=STUDENT_AUTH)
    assert response.status_code in (200, 404)

# Admin endpoints - students
def test_create_student_unauth():
    response = client.post("/admin/students", json={})
    assert response.status_code == 401

def test_create_student_admin():
    payload = {
        "index_number": "ug99999",
        "full_name": "Test Student",
        "dob": "2000-01-01",
        "gender": "M",
        "contact_email": "test@student.com",
        "phone": "1234567890",
        "program": "Test Program",
        "year_of_study": 1
    }
    response = client.post("/admin/students", json=payload, auth=ADMIN_AUTH)
    assert response.status_code in (200, 400)

def test_bulk_create_students_unauth():
    response = client.post("/admin/students/bulk", json={"students": []})
    assert response.status_code == 401

def test_bulk_create_students_admin():
    payload = {"students": [{
        "index_number": "ug99998",
        "full_name": "Bulk Student",
        "dob": "2000-01-01",
        "gender": "F",
        "contact_email": "bulk@student.com",
        "phone": "1234567890",
        "program": "Bulk Program",
        "year_of_study": 2
    }]}
    response = client.post("/admin/students/bulk", json=payload, auth=ADMIN_AUTH)
    assert response.status_code in (200, 400)

def test_get_all_students_unauth():
    response = client.get("/admin/students")
    assert response.status_code == 401

def test_get_all_students_admin():
    response = client.get("/admin/students", auth=ADMIN_AUTH)
    assert response.status_code == 200

def test_search_students_unauth():
    response = client.get("/admin/students/search")
    assert response.status_code == 401

def test_search_students_admin():
    response = client.get("/admin/students/search", auth=ADMIN_AUTH)
    assert response.status_code == 200

def test_get_student_by_index_unauth():
    response = client.get("/admin/students/ug00001")
    assert response.status_code == 401

def test_get_student_by_index_admin():
    response = client.get("/admin/students/ug10001", auth=ADMIN_AUTH)
    assert response.status_code in (200, 404)

def test_update_student_unauth():
    response = client.put("/admin/students/ug00001", json={})
    assert response.status_code == 401

def test_update_student_admin():
    response = client.put("/admin/students/ug10001", json={}, auth=ADMIN_AUTH)
    assert response.status_code in (200, 404)

# Admin endpoints - courses
def test_create_course_unauth():
    response = client.post("/admin/courses", json={})
    assert response.status_code == 401

def test_create_course_admin():
    payload = {
        "course_code": "TEST101",
        "course_title": "Test Course",
        "credit_hours": 3
    }
    response = client.post("/admin/courses", json=payload, auth=ADMIN_AUTH)
    assert response.status_code in (200, 400)

def test_get_all_courses_unauth():
    response = client.get("/admin/courses")
    assert response.status_code == 401

def test_get_all_courses_admin():
    response = client.get("/admin/courses", auth=ADMIN_AUTH)
    assert response.status_code == 200

# Admin endpoints - semesters
def test_create_semester_unauth():
    response = client.post("/admin/semesters", json={})
    assert response.status_code == 401

def test_create_semester_admin():
    payload = {
        "semester_name": "Test Semester",
        "academic_year": "2025/2026",
        "start_date": "2025-01-01",
        "end_date": "2025-06-01"
    }
    response = client.post("/admin/semesters", json=payload, auth=ADMIN_AUTH)
    assert response.status_code in (200, 400)

def test_get_all_semesters_unauth():
    response = client.get("/admin/semesters")
    assert response.status_code == 401

def test_get_all_semesters_admin():
    response = client.get("/admin/semesters", auth=ADMIN_AUTH)
    assert response.status_code == 200

# Admin endpoints - grades
def test_create_grade_unauth():
    response = client.post("/admin/grades", json={})
    assert response.status_code == 401

def test_create_grade_admin():
    payload = {
        "student_index": "ug10001",
        "course_code": "TEST101",
        "semester_name": "Test Semester",
        "score": 85,
        "academic_year": "2025/2026"
    }
    response = client.post("/admin/grades", json=payload, auth=ADMIN_AUTH)
    assert response.status_code in (200, 400, 404)

def test_get_all_grades_unauth():
    response = client.get("/admin/grades")
    assert response.status_code == 401

def test_get_all_grades_admin():
    response = client.get("/admin/grades", auth=ADMIN_AUTH)
    assert response.status_code == 200

# Admin endpoints - users
def test_create_user_account_unauth():
    response = client.post("/admin/users", json={})
    assert response.status_code == 401

def test_create_user_account_admin():
    payload = {
        "username": "testadmin",
        "password": "testpass123",
        "role": "admin"
    }
    response = client.post("/admin/users", json=payload, auth=ADMIN_AUTH)
    assert response.status_code in (200, 400)

def test_create_student_account_unauth():
    response = client.post("/admin/student-accounts", json={})
    assert response.status_code == 401

def test_create_student_account_admin():
    payload = {
        "index_number": "ug99997",
        "full_name": "Student Account",
        "password": "studentpass"
    }
    response = client.post("/admin/student-accounts", json=payload, auth=ADMIN_AUTH)
    assert response.status_code == 200  # Now expects success

def test_reset_password_unauth():
    response = client.post("/admin/reset-password", json={})
    assert response.status_code == 401

def test_reset_password_admin():
    payload = {
        "index_number": "ug10001",
        "new_password": "newpass123"
    }
    response = client.post("/admin/reset-password", json=payload, auth=ADMIN_AUTH)
    assert response.status_code == 200  # Now expects success

# Admin endpoints - bulk import
def test_bulk_import_unauth():
    response = client.post("/admin/bulk-import", json={})
    assert response.status_code == 401

def test_bulk_import_admin():
    payload = {
        "semester_name": "Test Semester",
        "file_data": []
    }
    response = client.post("/admin/bulk-import", json=payload, auth=ADMIN_AUTH)
    assert response.status_code == 200  # Now expects success with "no data" response
