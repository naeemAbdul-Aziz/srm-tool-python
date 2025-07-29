from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import os
import tempfile
from report_utils import export_summary_report_pdf, export_summary_report_txt
from auth import create_user, authenticate_user  # auth.py functions
from db import (
    fetch_all_records,
    fetch_student_by_index_number,
    insert_student_record,
    update_student_score,
    connect_to_db
)
from grade_util import calculate_grade
from file_handler import read_student_file
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
    score: int

class UpdateScore(BaseModel):
    score: int

class SignupData(BaseModel):
    username: str
    password: str
    role: str  # "admin" or "student"

class LoginData(BaseModel):
    username: str
    password: str

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
        student = fetch_student_by_index_number(index_number)
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
        student_data = student.dict()
        student_data['grade'] = calculate_grade(student_data['score'])

        conn = connect_to_db()
        if not conn:
            raise HTTPException(status_code=500, detail="Database connection failed")

        success = insert_student_record(conn, student_data)
        conn.close()

        if success:
            return {"message": "Student added successfully"}
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
        success = update_student_score(index_number, score, grade)
        if success:
            return {"message": "Student score updated successfully"}
        else:
            raise HTTPException(status_code=404, detail="Student not found or update failed")
    except Exception as e:
        logger.error(f"Error updating student score: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/students/upload")
def upload_student_file(file: UploadFile = File(...)):
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

        students = read_student_file(temp_path)
        inserted = 0
        for student in students:
            try:
                insert_student_record(conn, student)
                inserted += 1
            except Exception as e:
                logger.error(f"Error inserting student {student.get('index_number', '')}: {e}")

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

    # For students, verify index_number exists in student_results
    if role == "student":
        conn = connect_to_db()
        if not conn:
            raise HTTPException(status_code=500, detail="Database connection failed")
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM student_results WHERE index_number = %s", (user.username,))
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
        student = fetch_student_by_index_number(index_number)
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