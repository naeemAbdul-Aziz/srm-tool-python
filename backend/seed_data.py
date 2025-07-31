"""
seed_data.py
============

This script populates the database with initial data for testing and development purposes.
The data includes Ghanaian names and formats for courses, semesters, and students.
"""

from db import connect_to_db, insert_course, insert_semester, insert_student_profile, insert_grade
from datetime import datetime
from logger import get_logger
from db import fetch_student_by_index_number, fetch_course_by_code, fetch_semester_by_name
from grade_util import calculate_grade, get_grade_point

logger = get_logger(__name__)

def seed_courses(conn):
    """Populate the database with sample courses."""
    courses = [
        {"course_code": "MATH101", "course_title": "Basic Mathematics", "credit_hours": 3},
        {"course_code": "ENG102", "course_title": "English Composition", "credit_hours": 2},
        {"course_code": "HIST201", "course_title": "History of Ghana", "credit_hours": 3},
        {"course_code": "SCI301", "course_title": "Integrated Science", "credit_hours": 4},
        {"course_code": "ECON401", "course_title": "Economics Principles", "credit_hours": 3},
    ]

    for course in courses:
        try:
            insert_course(conn, course['course_code'], course['course_title'], course['credit_hours'])
            logger.info(f"Inserted course: {course['course_code']} - {course['course_title']}")
        except Exception as e:
            logger.error(f"Error inserting course {course['course_code']}: {e}")

def seed_semesters(conn):
    """Populate the database with sample semesters."""
    semesters = [
        {"semester_name": "Fall 2023", "start_date": datetime(2023, 9, 1), "end_date": datetime(2023, 12, 15)},
        {"semester_name": "Spring 2024", "start_date": datetime(2024, 1, 10), "end_date": datetime(2024, 5, 20)},
        {"semester_name": "Summer 2024", "start_date": datetime(2024, 6, 1), "end_date": datetime(2024, 8, 15)},
    ]

    for semester in semesters:
        try:
            insert_semester(conn, semester['semester_name'], semester['start_date'], semester['end_date'])
            logger.info(f"Inserted semester: {semester['semester_name']}")
        except Exception as e:
            logger.error(f"Error inserting semester {semester['semester_name']}: {e}")

def seed_students(conn):
    """Populate the database with sample students."""
    students = [
        {"index_number": "1001", "name": "John Doe", "dob": "2002-05-15", "gender": "Male", "program": "Computer Science", "year_of_study": 3, "contact_info": "john.doe@example.com"},
        {"index_number": "1002", "name": "Jane Smith", "dob": "2003-08-22", "gender": "Female", "program": "Information Technology", "year_of_study": 2, "contact_info": "jane.smith@example.com"},
        {"index_number": "1003", "name": "Kofi Mensah", "dob": "2004-11-10", "gender": "Male", "program": "Engineering", "year_of_study": 1, "contact_info": "kofi.mensah@example.com"},
        {"index_number": "1004", "name": "Akosua Asante", "dob": "2001-03-30", "gender": "Female", "program": "Business Administration", "year_of_study": 4, "contact_info": "akosua.asante@example.com"},
        {"index_number": "1005", "name": "Kojo Owusu", "dob": "2003-12-05", "gender": "Male", "program": "Mathematics", "year_of_study": 2, "contact_info": "kojo.owusu@example.com"}
    ]

    for student in students:
        try:
            insert_student_profile(conn, student['index_number'], student['name'], student['dob'], student['gender'], student['contact_info'], None, student['program'], student['year_of_study'])
            logger.info(f"Inserted student: {student['index_number']} - {student['name']}")
        except Exception as e:
            logger.error(f"Error inserting student {student['index_number']}: {e}")

def seed_grades(conn):
    """Populate the database with sample grades."""
    grades = [
        {"index_number": "1001", "course_code": "MATH101", "score": 85, "semester": "Fall 2023", "academic_year": "2023/2024"},
        {"index_number": "1002", "course_code": "ENG102", "score": 78, "semester": "Spring 2024", "academic_year": "2023/2024"},
        {"index_number": "1003", "course_code": "HIST201", "score": 92, "semester": "Summer 2024", "academic_year": "2023/2024"},
        {"index_number": "1004", "course_code": "SCI301", "score": 88, "semester": "Fall 2023", "academic_year": "2023/2024"},
        {"index_number": "1005", "course_code": "ECON401", "score": 65, "semester": "Spring 2024", "academic_year": "2023/2024"}
    ]

    for grade in grades:
        try:
            # Fetch IDs
            student = fetch_student_by_index_number(conn, grade['index_number'])
            course = fetch_course_by_code(conn, grade['course_code'])
            semester = fetch_semester_by_name(conn, grade['semester'])

            if not student or not course or not semester:
                logger.warning(f"Skipping grade for {grade['index_number']} in {grade['course_code']} due to missing data.")
                continue

            student_id = student['student_id']
            course_id = course['course_id']
            semester_id = semester['semester_id']

            # Calculate grade and grade point
            letter_grade = calculate_grade(grade['score'])
            grade_point = get_grade_point(grade['score'])

            # Insert grade
            insert_grade(conn, student_id, course_id, semester_id, grade['score'], letter_grade, grade_point, grade['academic_year'])
            logger.info(f"Inserted grade for student {grade['index_number']} in course {grade['course_code']}")
        except Exception as e:
            logger.error(f"Error inserting grade for student {grade['index_number']} in course {grade['course_code']}: {e}")

def seed_database():
    """Seed the database with initial data."""
    conn = connect_to_db()
    if conn:
        try:
            seed_courses(conn)
            seed_semesters(conn)
            seed_students(conn)
            seed_grades(conn)
            logger.info("Database seeding completed successfully.")
        except Exception as e:
            logger.error(f"Error during database seeding: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    seed_database()