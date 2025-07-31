from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from db import (
    connect_to_db, fetch_all_records, insert_student_profile, fetch_student_by_index_number,
    insert_course, fetch_all_courses, fetch_course_by_code, insert_semester, fetch_all_semesters,
    update_student_score, delete_course, delete_semester
)
from grade_util import calculate_grade, get_grade_point
from auth import authenticate_user

app = FastAPI()

# Pydantic Models
class Student(BaseModel):
    index_number: str
    name: str
    dob: Optional[str]
    gender: Optional[str]
    program: Optional[str]
    year_of_study: Optional[int]
    contact_info: Optional[str]

class Course(BaseModel):
    course_code: str
    course_title: str
    credit_hours: int

class Semester(BaseModel):
    semester_name: str
    start_date: str
    end_date: str

# Dependency for authentication
def get_current_user(role: str):
    def dependency(username: str, password: str):
        user = authenticate_user(username, password)
        if not user or user['role'] != role:
            raise HTTPException(status_code=403, detail="Access forbidden")
        return user
    return dependency

# Admin Endpoints
@app.post("/admin/students", dependencies=[Depends(get_current_user("admin"))])
def add_student(student: Student):
    conn = connect_to_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        insert_student_profile(conn, **student.dict())
        return {"message": "Student added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/admin/students", dependencies=[Depends(get_current_user("admin"))])
def get_all_students():
    conn = connect_to_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        students = fetch_all_records(conn)
        return students
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.post("/admin/courses", dependencies=[Depends(get_current_user("admin"))])
def add_course(course: Course):
    conn = connect_to_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        insert_course(conn, **course.dict())
        return {"message": "Course added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/admin/courses", dependencies=[Depends(get_current_user("admin"))])
def get_all_courses():
    conn = connect_to_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        courses = fetch_all_courses(conn)
        return courses
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.post("/admin/semesters", dependencies=[Depends(get_current_user("admin"))])
def add_semester(semester: Semester):
    conn = connect_to_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        insert_semester(conn, **semester.dict())
        return {"message": "Semester added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/admin/semesters", dependencies=[Depends(get_current_user("admin"))])
def get_all_semesters():
    conn = connect_to_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        semesters = fetch_all_semesters(conn)
        return semesters
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# Student Endpoints
@app.get("/student/grades", dependencies=[Depends(get_current_user("student"))])
def get_grades(index_number: str):
    conn = connect_to_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        student = fetch_student_by_index_number(conn, index_number)
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        return student['grades']
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/student/profile", dependencies=[Depends(get_current_user("student"))])
def get_profile(index_number: str):
    conn = connect_to_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        student = fetch_student_by_index_number(conn, index_number)
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        return student['profile']
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()