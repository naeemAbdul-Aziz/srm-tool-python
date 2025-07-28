from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import os
from fastapi.responses import JSONResponse
from pydantic import BaseModel
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
    allow_origins=["*"],  # Or specify ["http://localhost:5500"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = get_logger(__name__)

class Student(BaseModel):
    index_number: str
    full_name: str
    course: str
    score: int

class UpdateScore(BaseModel):
    score: int

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
        # Allow both .txt and .csv files
        if not file.filename or not (file.filename.endswith('.txt') or file.filename.endswith('.csv')):
            raise HTTPException(status_code=400, detail="Only .txt or .csv files are allowed")

        # Save uploaded content to temp file
        contents = file.file.read().decode("utf-8")
        temp_path = "temp_upload.txt"
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(contents)

        # Connect to database
        conn = connect_to_db()
        if not conn:
            raise HTTPException(status_code=500, detail="Database connection failed")

        # Parse file contents
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
