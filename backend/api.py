from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import tempfile
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from bulk_importer import bulk_import_from_file
from report_utils import export_summary_report_pdf, export_summary_report_txt
from auth import create_user, authenticate_user  # auth.py functions
from db import (
    fetch_all_records,
    fetch_student_by_index_number,
    insert_student_profile,
    insert_grade,
    insert_complete_student_record,
    update_student_score,
    connect_to_db,
    create_tables,
    create_enhanced_tables,
    # Course management functions
    insert_course,
    fetch_all_courses,
    fetch_course_by_code,
    update_course,
    delete_course,
    # Semester management functions
    insert_semester,
    fetch_all_semesters,
    fetch_current_semester,
    set_current_semester
)
from grade_util import calculate_grade
from file_handler import read_student_records
from logger import get_logger

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = get_logger(__name__)

# --- Data Models ---

class Student(BaseModel):
    index_number: str
    full_name: str
    course: str
    score: float
    # Optional fields for enhanced functionality
    program: Optional[str] = None
    year_of_study: Optional[int] = 1
    contact_info: Optional[str] = None
    course_code: Optional[str] = "GENERAL"
    course_title: Optional[str] = None
    credit_hours: Optional[int] = 3
    semester: Optional[str] = "Fall 2024"
    academic_year: Optional[str] = "2024-2025"

class UpdateScore(BaseModel):
    score: float
    course_code: str = "GENERAL"  # default course code

class SignupData(BaseModel):
    username: str
    password: str
    role: str  # "admin" or "student"

class LoginData(BaseModel):
    username: str
    password: str

# Course Management Models
class Course(BaseModel):
    course_code: str
    course_title: str
    credit_hours: int = 3
    department: Optional[str] = None
    instructor: Optional[str] = None
    description: Optional[str] = None

class CourseUpdate(BaseModel):
    course_title: Optional[str] = None
    credit_hours: Optional[int] = None
    department: Optional[str] = None
    instructor: Optional[str] = None
    description: Optional[str] = None

# Semester Management Models
class Semester(BaseModel):
    semester_id: str  # e.g., "FALL2024"
    semester_name: str  # e.g., "Fall 2024"
    academic_year: str  # e.g., "2024-2025"
    start_date: str  # ISO format date
    end_date: str  # ISO format date
    is_current: bool = False

class SemesterUpdate(BaseModel):
    semester_name: Optional[str] = None
    academic_year: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_current: Optional[bool] = None

# Enhanced Grade Management Models
class EnhancedGrade(BaseModel):
    student_index_number: str
    course_code: str
    semester_id: str
    score: float
    grade_letter: Optional[str] = None
    grade_points: Optional[float] = None
    assessment_type: str = "final"  # "final", "midterm", "quiz", "assignment"
    weight: float = 1.0  # for weighted averages

class GradeUpdate(BaseModel):
    score: Optional[float] = None
    grade_letter: Optional[str] = None
    assessment_type: Optional[str] = None
    weight: Optional[float] = None

# --- Student Endpoints ---

@app.get("/students")
def get_all_students():
    try:
        students = fetch_all_records()
        return students
    except Exception as e:
        logger.error(f"Failed to fetch students: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/students/{index_number}")
def get_student_by_index(index_number: str):
    try:
        conn = connect_to_db()
        if not conn:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        student = fetch_student_by_index_number(conn, index_number)
        conn.close()
        
        if student:
            return student
        else:
            raise HTTPException(status_code=404, detail="Student not found")
    except Exception as e:
        logger.error(f"Error fetching student: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/students", status_code=201)
def add_student(student: Student):
    try:
        # Map API model to database format
        student_data = {
            "index_number": student.index_number,
            "name": student.full_name,  # Map full_name to name
            "program": student.program or "General Program",
            "year_of_study": student.year_of_study or 1,
            "contact_info": student.contact_info or "Not provided",
            "course_code": student.course_code or "GENERAL",
            "course_title": student.course_title or student.course,  # Use course_title or fallback to course
            "score": float(student.score),
            "credit_hours": student.credit_hours or 3,
            "semester": student.semester or "Fall 2024",
            "academic_year": student.academic_year or "2024-2025"
        }
        
        # Calculate letter grade
        student_data['grade'] = calculate_grade(student_data['score'])

        conn = connect_to_db()
        if not conn:
            raise HTTPException(status_code=500, detail="Database connection failed")

        success = insert_complete_student_record(conn, student_data)
        conn.close()

        if success:
            return {
                "message": "Student added successfully",
                "student_id": student_data["index_number"],
                "grade": student_data['grade']
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to insert student")
    except Exception as e:
        logger.error(f"Error in add_student: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/students/{index_number}")
def update_score(index_number: str, update: UpdateScore):
    score = update.score
    if not (0 <= score <= 100):
        raise HTTPException(status_code=400, detail="Score must be between 0 and 100")
    try:
        grade = calculate_grade(score)
        success = update_student_score(index_number, update.course_code, score, grade)
        if success:
            return {"message": "Student score updated successfully"}
        else:
            raise HTTPException(status_code=404, detail="Student not found or update failed")
    except Exception as e:
        logger.error(f"Error updating student score: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/students/upload")
def upload_student_file_basic(file: UploadFile = File(...)):
    try:
        if not file.filename or not (file.filename.endswith('.txt') or file.filename.endswith('.csv')):
            raise HTTPException(status_code=400, detail="Only .txt or .csv files are allowed")

        contents = file.file.read().decode("utf-8")
        temp_path = "temp_upload.txt"
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(contents)

        conn = connect_to_db()
        if not conn:
            raise HTTPException(status_code=500, detail="Database connection failed")

        students = read_student_records(temp_path)
        inserted = 0
        for student in students:
            try:
                insert_complete_student_record(conn, student)
                inserted += 1
            except Exception as e:
                logger.error(f"error inserting student {student.get('index_number', '') if isinstance(student, dict) else 'unknown'}: {e}")

        conn.close()
        return {"message": f"{inserted} students uploaded successfully."}

    except Exception as e:
        logger.error(f"File upload failed: {e}")
        raise HTTPException(status_code=500, detail="File upload processing failed")
    finally:
        try:
            file.file.close()
            if os.path.exists("temp_upload.txt"):
                os.remove("temp_upload.txt")
        except Exception:
            pass

# --- Authentication Endpoints ---

@app.post("/signup")
def signup(user: SignupData):
    role = user.role.lower()
    if role not in ("admin", "student"):
        raise HTTPException(status_code=400, detail="Role must be 'admin' or 'student'")

    # for students, verify index_number exists in student_profiles
    if role == "student":
        conn = connect_to_db()
        if not conn:
            raise HTTPException(status_code=500, detail="Database connection failed")
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM student_profiles WHERE index_number = %s", (user.username,))
                if cur.fetchone() is None:
                    raise HTTPException(status_code=400, detail="Index number not found in student records. Please contact admin.")
        except Exception as e:
            logger.error(f"Error verifying student index number on signup: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
        finally:
            conn.close()

    success = create_user(user.username, user.password, role)
    if success:
        return {"message": "User created successfully."}
    else:
        raise HTTPException(status_code=500, detail="User creation failed.")

@app.post("/login")
def login(user: LoginData):
    role = authenticate_user(user.username, user.password)
    if role:
        return {"message": "Login successful.", "username": user.username, "role": role}
    else:
        raise HTTPException(status_code=401, detail="Invalid username or password.")


# --- Export Endpoints ---

@app.get("/export/{format}")
def export_full_summary(format: str):
    """
    Admin-only export of all records to TXT or PDF.
    """
    if format.lower() not in ("pdf", "txt"):
        raise HTTPException(status_code=400, detail="Format must be 'pdf' or 'txt'")
    try:
        records = fetch_all_records()
        if not records:
            raise HTTPException(status_code=404, detail="No student records found")

        suffix = ".pdf" if format.lower() == "pdf" else ".txt"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            filepath = tmp.name
            if format.lower() == "pdf":
                success = export_summary_report_pdf(records, filepath)
            else:
                success = export_summary_report_txt(records, filepath)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to generate export file")

        return FileResponse(filepath, media_type="application/octet-stream", filename=f"student_summary{suffix}")
    except Exception as e:
        logger.error(f"Export failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/export/{index_number}/{format}")
def export_individual_student(index_number: str, format: str):
    """
    Student-only export of their own result to TXT or PDF.
    """
    if format.lower() not in ("pdf", "txt"):
        raise HTTPException(status_code=400, detail="Format must be 'pdf' or 'txt'")
    try:
        conn = connect_to_db()
        if not conn:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        student = fetch_student_by_index_number(conn, index_number)
        conn.close()
        
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")

        suffix = ".pdf" if format.lower() == "pdf" else ".txt"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            filepath = tmp.name
            records = [student]
            if format.lower() == "pdf":
                success = export_summary_report_pdf(records, filepath)
            else:
                success = export_summary_report_txt(records, filepath)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to generate export file")

        return FileResponse(filepath, media_type="application/octet-stream", filename=f"{index_number}_report{suffix}")
    except Exception as e:
        logger.error(f"Export for student {index_number} failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

#bulk import endpoint
@app.post("/students/upload")
def upload_student_file(file: UploadFile = File(...)):
    try:
        if not file.filename or not (file.filename.endswith('.txt') or file.filename.endswith('.csv')):
            raise HTTPException(status_code=400, detail="Only .txt or .csv files are allowed")

        contents = file.file.read().decode("utf-8")
        temp_path = "temp_upload.txt"
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(contents)

        summary = bulk_import_from_file(temp_path)

        return {
            "message": summary["message"],
            "total": summary["total"],
            "successful": summary["successful"],
            "skipped": summary["skipped"],
            "errors": summary["errors"]
        }

    except Exception as e:
        logger.error(f"File upload failed: {e}")
        raise HTTPException(status_code=500, detail="File upload processing failed")
    finally:
        try:
            file.file.close()
            if os.path.exists("temp_upload.txt"):
                os.remove("temp_upload.txt")
        except Exception:
            pass

# --- Course Management Endpoints ---

@app.get("/courses/")
def get_all_courses():
    """Get all courses"""
    try:
        courses = fetch_all_courses()
        return {"courses": courses}
    except Exception as e:
        logger.error(f"Error fetching courses: {e}")
        raise HTTPException(status_code=500, detail="Error fetching courses")

@app.post("/courses/")
def create_course(course: Course):
    """Create a new course"""
    try:
        conn = connect_to_db()
        if not conn:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        course_data = {
            "course_code": course.course_code,
            "course_title": course.course_title,
            "credit_hours": course.credit_hours,
            "department": course.department,
            "instructor": course.instructor,
            "description": course.description
        }
        
        if insert_course(conn, course_data):
            conn.close()
            return {"message": f"Course {course.course_code} created successfully"}
        else:
            conn.close()
            raise HTTPException(status_code=400, detail="Failed to create course")
    except Exception as e:
        logger.error(f"Error creating course: {e}")
        raise HTTPException(status_code=500, detail="Error creating course")

@app.get("/courses/{course_code}")
def get_course(course_code: str):
    """Get a specific course by code"""
    try:
        course = fetch_course_by_code(course_code.upper())
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        return course
    except Exception as e:
        logger.error(f"Error fetching course {course_code}: {e}")
        raise HTTPException(status_code=500, detail="Error fetching course")

@app.put("/courses/{course_code}")
def update_course_endpoint(course_code: str, updates: Dict[str, Any]):
    """Update a course"""
    try:
        if update_course(course_code.upper(), updates):
            return {"message": f"Course {course_code} updated successfully"}
        else:
            raise HTTPException(status_code=404, detail="Course not found or update failed")
    except Exception as e:
        logger.error(f"Error updating course {course_code}: {e}")
        raise HTTPException(status_code=500, detail="Error updating course")

@app.delete("/courses/{course_code}")
def delete_course_endpoint(course_code: str):
    """Delete a course"""
    try:
        if delete_course(course_code.upper()):
            return {"message": f"Course {course_code} deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Course not found or delete failed")
    except Exception as e:
        logger.error(f"Error deleting course {course_code}: {e}")
        raise HTTPException(status_code=500, detail="Error deleting course")

# --- Semester Management Endpoints ---

@app.get("/semesters/")
def get_all_semesters():
    """Get all semesters"""
    try:
        semesters = fetch_all_semesters()
        return {"semesters": semesters}
    except Exception as e:
        logger.error(f"Error fetching semesters: {e}")
        raise HTTPException(status_code=500, detail="Error fetching semesters")

@app.post("/semesters/")
def create_semester(semester: Semester):
    """Create a new semester"""
    try:
        conn = connect_to_db()
        if not conn:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        semester_data = {
            "semester_id": semester.semester_id,
            "semester_name": semester.semester_name,
            "academic_year": semester.academic_year,
            "start_date": semester.start_date,
            "end_date": semester.end_date,
            "is_current": semester.is_current
        }
        
        if insert_semester(conn, semester_data):
            conn.close()
            return {"message": f"Semester {semester.semester_id} created successfully"}
        else:
            conn.close()
            raise HTTPException(status_code=400, detail="Failed to create semester")
    except Exception as e:
        logger.error(f"Error creating semester: {e}")
        raise HTTPException(status_code=500, detail="Error creating semester")

@app.get("/semesters/current")
def get_current_semester():
    """Get the current semester"""
    try:
        current = fetch_current_semester()
        if not current:
            raise HTTPException(status_code=404, detail="No current semester set")
        return current
    except Exception as e:
        logger.error(f"Error fetching current semester: {e}")
        raise HTTPException(status_code=500, detail="Error fetching current semester")

@app.put("/semesters/{semester_id}/set-current")
def set_current_semester_endpoint(semester_id: str):
    """Set a semester as current"""
    try:
        if set_current_semester(semester_id.upper()):
            return {"message": f"Semester {semester_id} set as current"}
        else:
            raise HTTPException(status_code=404, detail="Semester not found or update failed")
    except Exception as e:
        logger.error(f"Error setting current semester {semester_id}: {e}")
        raise HTTPException(status_code=500, detail="Error setting current semester")

@app.put("/semesters/{semester_id}")
def update_semester_endpoint(semester_id: str, updates: Dict[str, Any]):
    """Update a semester"""
    try:
        # Implementation would depend on having an update_semester function in db.py
        raise HTTPException(status_code=501, detail="Update semester not implemented yet")
    except Exception as e:
        logger.error(f"Error updating semester {semester_id}: {e}")
        raise HTTPException(status_code=500, detail="Error updating semester")

@app.delete("/semesters/{semester_id}")
def delete_semester_endpoint(semester_id: str):
    """Delete a semester"""
    try:
        # Implementation would depend on having a delete_semester function in db.py
        raise HTTPException(status_code=501, detail="Delete semester not implemented yet")
    except Exception as e:
        logger.error(f"Error deleting semester {semester_id}: {e}")
        raise HTTPException(status_code=500, detail="Error deleting semester")