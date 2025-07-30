import psycopg2
import os
from dotenv import load_dotenv
import logging
from psycopg2.extras import RealDictCursor
from config import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT

load_dotenv()
logger = logging.getLogger(__name__)

def connect_to_db():
    """establish connection to the postgresql database"""
    try:
        logger.debug("attempting database connection...")
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        logger.info("database connection established successfully")
        return conn
    except psycopg2.OperationalError as e:
        logger.error(f"database connection failed - operational error: {e}")
        return None
    except Exception as e:
        logger.error(f"database connection failed - unexpected error: {e}")
        return None

def create_tables():
    """create database tables if they don't exist"""
    logger.info("creating database tables...")
    conn = connect_to_db()
    if conn is None:
        logger.error("cannot create tables - no database connection")
        return

    try:
        cursor = conn.cursor()

        # new student profile table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS student_profiles (
                index_number VARCHAR(20) PRIMARY KEY,
                name VARCHAR(100),
                program VARCHAR(100),
                year_of_study INTEGER,
                contact_info VARCHAR(100)
            );
        """)

        # grades table - allows multiple course entries per student
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS grades (
                id SERIAL PRIMARY KEY,
                index_number VARCHAR(20) REFERENCES student_profiles(index_number) ON DELETE CASCADE,
                course_code VARCHAR(20),
                course_title VARCHAR(100),
                score FLOAT,
                credit_hours INTEGER,
                letter_grade VARCHAR(2),
                semester VARCHAR(20),
                academic_year VARCHAR(20)
            );
        """)

        conn.commit()
        logger.info("tables created or confirmed successfully")
    except psycopg2.Error as e:
        logger.error(f"database error creating tables: {e}")
        conn.rollback()
    except Exception as e:
        logger.error(f"unexpected error creating tables: {e}")
        conn.rollback()
    finally:
        conn.close()

def create_enhanced_tables():
    """Create enhanced database tables for courses, semesters, and improved grades"""
    logger.info("Creating enhanced database tables...")
    conn = connect_to_db()
    if conn is None:
        logger.error("Cannot create enhanced tables - no database connection")
        return False

    try:
        cursor = conn.cursor()

        # Courses table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS courses (
                course_code VARCHAR(20) PRIMARY KEY,
                course_title VARCHAR(200) NOT NULL,
                credit_hours INTEGER DEFAULT 3,
                department VARCHAR(100),
                instructor VARCHAR(100),
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Semesters table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS semesters (
                semester_id VARCHAR(20) PRIMARY KEY,
                semester_name VARCHAR(50) NOT NULL,
                academic_year VARCHAR(20) NOT NULL,
                start_date DATE,
                end_date DATE,
                is_current BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Enhanced grades table (keep existing for compatibility, add indexes)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_grades_student_course 
            ON grades(index_number, course_code);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_grades_semester 
            ON grades(semester, academic_year);
        """)

        # Detailed assessments table for enhanced grade management
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assessments (
                id SERIAL PRIMARY KEY,
                index_number VARCHAR(20) REFERENCES student_profiles(index_number) ON DELETE CASCADE,
                course_code VARCHAR(20) REFERENCES courses(course_code) ON DELETE CASCADE,
                semester_id VARCHAR(20) REFERENCES semesters(semester_id) ON DELETE CASCADE,
                assessment_type VARCHAR(50) DEFAULT 'final',
                score FLOAT NOT NULL,
                max_score FLOAT DEFAULT 100,
                weight FLOAT DEFAULT 1.0,
                grade_letter VARCHAR(2),
                grade_points FLOAT,
                assessment_date DATE DEFAULT CURRENT_DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Student enrollments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS enrollments (
                id SERIAL PRIMARY KEY,
                index_number VARCHAR(20) REFERENCES student_profiles(index_number) ON DELETE CASCADE,
                course_code VARCHAR(20) REFERENCES courses(course_code) ON DELETE CASCADE,
                semester_id VARCHAR(20) REFERENCES semesters(semester_id) ON DELETE CASCADE,
                enrollment_date DATE DEFAULT CURRENT_DATE,
                status VARCHAR(20) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(index_number, course_code, semester_id)
            );
        """)

        conn.commit()
        logger.info("Enhanced tables created or confirmed successfully")
        return True
    except psycopg2.Error as e:
        logger.error(f"Database error creating enhanced tables: {e}")
        conn.rollback()
        return False
    except Exception as e:
        logger.error(f"Unexpected error creating enhanced tables: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def drop_legacy_tables():
    """drop the old student_results table - run this once to clean up legacy table"""
    logger.info("dropping legacy student_results table...")
    conn = connect_to_db()
    if conn is None:
        logger.error("cannot drop tables - no database connection")
        return False

    try:
        cursor = conn.cursor()
        
        # drop the legacy table
        cursor.execute("DROP TABLE IF EXISTS student_results CASCADE;")
        
        conn.commit()
        logger.info("legacy student_results table dropped successfully")
        return True
    except psycopg2.Error as e:
        logger.error(f"database error dropping legacy table: {e}")
        conn.rollback()
        return False
    except Exception as e:
        logger.error(f"unexpected error dropping legacy table: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def insert_complete_student_record(conn, student_data):
    """insert a complete student record (profile + grade) for backwards compatibility with api"""
    try:
        # prepare profile data
        profile_data = {
            "index_number": student_data["index_number"],
            "name": student_data["name"],
            "program": student_data.get("program", "Unknown"),
            "year_of_study": student_data.get("year_of_study", 1),
            "contact_info": student_data.get("contact_info", "Not provided")
        }
        
        # prepare grade data with defaults
        grade_data = {
            "index_number": student_data["index_number"],
            "course_code": student_data.get("course_code", "GENERAL"),
            "course_title": student_data.get("course_title", "General Assessment"),
            "score": student_data["score"],
            "credit_hours": student_data.get("credit_hours", 3),
            "letter_grade": student_data["grade"],
            "semester": student_data.get("semester", "Fall 2024"),
            "academic_year": student_data.get("academic_year", "2024-2025")
        }
        
        # insert profile first
        if not insert_student_profile(conn, profile_data):
            return False
            
        # then insert grade
        if not insert_grade(conn, grade_data):
            return False
            
        logger.info(f"complete student record inserted for {student_data['index_number']}")
        return True
        
    except Exception as e:
        logger.error(f"error inserting complete student record: {e}")
        return False

# insert student profile into modern table
def insert_student_profile(conn, profile):
    """insert or update student profile in the student_profiles table"""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO student_profiles (index_number, name, program, year_of_study, contact_info)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (index_number) DO UPDATE
            SET name = EXCLUDED.name,
                program = EXCLUDED.program,
                year_of_study = EXCLUDED.year_of_study,
                contact_info = EXCLUDED.contact_info;
        """, (
            profile["index_number"],
            profile["name"],
            profile["program"],
            profile["year_of_study"],
            profile["contact_info"]
        ))
        conn.commit()
        logger.info(f"student profile inserted/updated for {profile['index_number']}")
        return True
    except psycopg2.Error as e:
        logger.error(f"database error inserting student profile: {e}")
        return False
    except Exception as e:
        logger.error(f"unexpected error inserting student profile: {e}")
        return False

# insert a course-grade entry
def insert_grade(conn, grade):
    """insert a grade record for a specific course"""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO grades (
                index_number, course_code, course_title, score,
                credit_hours, letter_grade, semester, academic_year
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """, (
            grade["index_number"],
            grade["course_code"],
            grade["course_title"],
            grade["score"],
            grade["credit_hours"],
            grade["letter_grade"],
            grade["semester"],
            grade["academic_year"]
        ))
        conn.commit()
        logger.info(f"grade inserted for {grade['index_number']}, course {grade['course_code']}")
        return True
    except psycopg2.Error as e:
        logger.error(f"database error inserting grade: {e}")
        return False
    except Exception as e:
        logger.error(f"unexpected error inserting grade: {e}")
        return False

# Fetch full student profile by index number
def fetch_student_by_index_number(conn, index_number):
    try:
        cursor = conn.cursor()
        
        # Fetch profile
        cursor.execute("""
            SELECT name, program, year_of_study, contact_info
            FROM student_profiles
            WHERE index_number = %s;
        """, (index_number,))
        profile = cursor.fetchone()

        # Fetch grades
        cursor.execute("""
            SELECT course_code, course_title, score, credit_hours, letter_grade, semester, academic_year
            FROM grades
            WHERE index_number = %s;
        """, (index_number,))
        grades = cursor.fetchall()

        return {
            "profile": {
                "index_number": index_number,
                "name": profile[0] if profile else None,
                "program": profile[1] if profile else None,
                "year_of_study": profile[2] if profile else None,
                "contact_info": profile[3] if profile else None
            },
            "grades": [
                {
                    "course_code": g[0],
                    "course_title": g[1],
                    "score": g[2],
                    "credit_hours": g[3],
                    "letter_grade": g[4],
                    "semester": g[5],
                    "academic_year": g[6]
                } for g in grades
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching student by index: {e}")
        return None


# ========== Fetch all student records ==========
def fetch_all_records():
    conn = connect_to_db()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        sp.index_number,
                        sp.name,
                        sp.program,
                        sp.year_of_study,
                        sp.contact_info,
                        g.course_code,
                        g.course_title,
                        g.score,
                        g.letter_grade,
                        g.credit_hours,
                        g.semester,
                        g.academic_year
                    FROM student_profiles sp
                    LEFT JOIN grades g ON sp.index_number = g.index_number
                    ORDER BY sp.index_number, g.semester, g.course_code
                """)
                records = cur.fetchall()
                return records
        except Exception as e:
            logger.error(f"Error fetching records: {e}")
            return []
        finally:
            conn.close()
    return []

# ========== Update a student's score ==========
def update_student_score(index_number, course_code, new_score, new_grade):
    conn = connect_to_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE grades
                    SET score = %s, letter_grade = %s
                    WHERE index_number = %s AND course_code = %s
                """, (new_score, new_grade, index_number, course_code))
                conn.commit()
                return cur.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating score: {e}")
            return False
        finally:
            conn.close()
    return False

# ========== Fetch results for a single student ==========
def fetch_student_results(index_number):
    """
    Legacy function - use fetch_student_by_index_number instead
    """
    conn = connect_to_db()
    if conn:
        try:
            student_data = fetch_student_by_index_number(conn, index_number)
            return student_data["grades"] if student_data else []
        except Exception as e:
            logger.error(f"Error fetching student results: {e}")
            return []
        finally:
            conn.close()
    return []

# ========== Fetch results by semester ==========
def fetch_results_by_semester(semester):
    conn = connect_to_db()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        sp.name,
                        g.index_number,
                        g.course_code,
                        g.course_title,
                        g.score,
                        g.letter_grade,
                        g.semester,
                        g.academic_year
                    FROM grades g
                    JOIN student_profiles sp ON g.index_number = sp.index_number
                    WHERE g.semester = %s
                    ORDER BY sp.name, g.course_code
                """, (semester,))
                return cur.fetchall()
        finally:
            conn.close()
    return []

# ===== COURSE MANAGEMENT FUNCTIONS =====

def insert_course(conn, course_data):
    """Insert a new course"""
    try:
        cursor = conn.cursor()
        query = """
            INSERT INTO courses (course_code, course_title, credit_hours, department, instructor, description)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (course_code) DO UPDATE SET
                course_title = EXCLUDED.course_title,
                credit_hours = EXCLUDED.credit_hours,
                department = EXCLUDED.department,
                instructor = EXCLUDED.instructor,
                description = EXCLUDED.description,
                updated_at = CURRENT_TIMESTAMP
        """
        cursor.execute(query, (
            course_data["course_code"],
            course_data["course_title"],
            course_data.get("credit_hours", 3),
            course_data.get("department"),
            course_data.get("instructor"),
            course_data.get("description")
        ))
        logger.info(f"Course {course_data['course_code']} inserted/updated successfully")
        return True
    except psycopg2.Error as e:
        logger.error(f"Database error inserting course: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error inserting course: {e}")
        return False

def fetch_all_courses():
    """Fetch all courses"""
    conn = connect_to_db()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM courses ORDER BY course_code")
                return cur.fetchall()
        except Exception as e:
            logger.error(f"Error fetching courses: {e}")
            return []
        finally:
            conn.close()
    return []

def fetch_course_by_code(course_code):
    """Fetch a specific course by code"""
    conn = connect_to_db()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM courses WHERE course_code = %s", (course_code,))
                return cur.fetchone()
        except Exception as e:
            logger.error(f"Error fetching course {course_code}: {e}")
            return None
        finally:
            conn.close()
    return None

def update_course(course_code, updates):
    """Update a course"""
    conn = connect_to_db()
    if conn:
        try:
            cursor = conn.cursor()
            set_clauses = []
            values = []
            
            for field, value in updates.items():
                if value is not None:
                    set_clauses.append(f"{field} = %s")
                    values.append(value)
            
            if set_clauses:
                set_clauses.append("updated_at = CURRENT_TIMESTAMP")
                values.append(course_code)
                
                query = f"UPDATE courses SET {', '.join(set_clauses)} WHERE course_code = %s"
                cursor.execute(query, values)
                
                if cursor.rowcount > 0:
                    conn.commit()
                    logger.info(f"Course {course_code} updated successfully")
                    return True
                else:
                    logger.warning(f"No course found with code {course_code}")
                    return False
            return True
        except Exception as e:
            logger.error(f"Error updating course {course_code}: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    return False

def delete_course(course_code):
    """Delete a course"""
    conn = connect_to_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM courses WHERE course_code = %s", (course_code,))
            
            if cursor.rowcount > 0:
                conn.commit()
                logger.info(f"Course {course_code} deleted successfully")
                return True
            else:
                logger.warning(f"No course found with code {course_code}")
                return False
        except Exception as e:
            logger.error(f"Error deleting course {course_code}: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    return False

# ===== SEMESTER MANAGEMENT FUNCTIONS =====

def insert_semester(conn, semester_data):
    """Insert a new semester"""
    try:
        cursor = conn.cursor()
        
        # If this is set as current, unset all others first
        if semester_data.get("is_current", False):
            cursor.execute("UPDATE semesters SET is_current = FALSE")
        
        query = """
            INSERT INTO semesters (semester_id, semester_name, academic_year, start_date, end_date, is_current)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (semester_id) DO UPDATE SET
                semester_name = EXCLUDED.semester_name,
                academic_year = EXCLUDED.academic_year,
                start_date = EXCLUDED.start_date,
                end_date = EXCLUDED.end_date,
                is_current = EXCLUDED.is_current,
                updated_at = CURRENT_TIMESTAMP
        """
        cursor.execute(query, (
            semester_data["semester_id"],
            semester_data["semester_name"],
            semester_data["academic_year"],
            semester_data.get("start_date"),
            semester_data.get("end_date"),
            semester_data.get("is_current", False)
        ))
        logger.info(f"Semester {semester_data['semester_id']} inserted/updated successfully")
        return True
    except psycopg2.Error as e:
        logger.error(f"Database error inserting semester: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error inserting semester: {e}")
        return False

def fetch_all_semesters():
    """Fetch all semesters"""
    conn = connect_to_db()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM semesters ORDER BY academic_year DESC, semester_id")
                return cur.fetchall()
        except Exception as e:
            logger.error(f"Error fetching semesters: {e}")
            return []
        finally:
            conn.close()
    return []

def fetch_current_semester():
    """Fetch the current active semester"""
    conn = connect_to_db()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM semesters WHERE is_current = TRUE LIMIT 1")
                return cur.fetchone()
        except Exception as e:
            logger.error(f"Error fetching current semester: {e}")
            return None
        finally:
            conn.close()
    return None

def set_current_semester(semester_id):
    """Set a semester as the current active semester"""
    conn = connect_to_db()
    if conn:
        try:
            cursor = conn.cursor()
            
            # First, unset all current semesters
            cursor.execute("UPDATE semesters SET is_current = FALSE")
            
            # Then set the specified one as current
            cursor.execute(
                "UPDATE semesters SET is_current = TRUE, updated_at = CURRENT_TIMESTAMP WHERE semester_id = %s",
                (semester_id,)
            )
            
            if cursor.rowcount > 0:
                conn.commit()
                logger.info(f"Semester {semester_id} set as current")
                return True
            else:
                logger.warning(f"No semester found with ID {semester_id}")
                conn.rollback()
                return False
        except Exception as e:
            logger.error(f"Error setting current semester: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    return False
