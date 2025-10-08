import psycopg2
import os
from datetime import datetime
from dotenv import load_dotenv
import logging
from psycopg2.extras import RealDictCursor
try:  # Prefer relative imports when part of package
    from .config import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT
    from .grade_util import calculate_grade, get_grade_point
except ImportError:  # Fallback for direct execution (python db.py)
    from config import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT
    from grade_util import calculate_grade, get_grade_point

load_dotenv()
logger = logging.getLogger(__name__)

def connect_to_db():
    """establish connection to the postgresql database"""
    try:
        logger.debug("Attempting database connection...")
        logger.debug(f"[DB_CONNECT] DB_NAME: {DB_NAME}, DB_USER: {DB_USER}, DB_HOST: {DB_HOST}, DB_PORT: {DB_PORT}")

        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        logger.info("Database connection established successfully.")
        return conn
    # Improved error handling
    except psycopg2.OperationalError as e:
        logger.error(f"OperationalError during database connection: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during database connection: {e}")
        return None

def create_table(conn, table_name):
    """Create a specific table if it doesn't exist."""
    if conn is None:
        logger.error("No database connection to create tables.")
        return False
    try:
        with conn.cursor() as cur:
            cur.execute(TABLES[table_name])
            logger.info(f"{table_name} table checked/created.")
            return True
    except Exception as e:
        logger.error(f"Error creating {table_name} table: {e}")
        return False

# Modularized table creation logic
TABLES = {
    "users": """
        CREATE TABLE IF NOT EXISTS users (
            user_id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            role VARCHAR(50) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    """,
    "student_profiles": """
        CREATE TABLE IF NOT EXISTS student_profiles (
            student_id SERIAL PRIMARY KEY,
            index_number VARCHAR(20) UNIQUE NOT NULL,
            full_name VARCHAR(255) NOT NULL,
            dob DATE,
            gender VARCHAR(10),
            contact_email VARCHAR(255),
            contact_phone VARCHAR(20),
            program VARCHAR(100),
            year_of_study INT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    """,
    "courses": """
        CREATE TABLE IF NOT EXISTS courses (
            course_id SERIAL PRIMARY KEY,
            course_code VARCHAR(20) UNIQUE NOT NULL,
            course_title VARCHAR(255) NOT NULL,
            credit_hours INT NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    """,
    "semesters": """
        CREATE TABLE IF NOT EXISTS semesters (
            semester_id SERIAL PRIMARY KEY,
            semester_name VARCHAR(100) UNIQUE NOT NULL,
            academic_year VARCHAR(20),
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            is_current BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    """,
    "notifications": """
        CREATE TABLE IF NOT EXISTS notifications (
            notification_id SERIAL PRIMARY KEY,
            type VARCHAR(40) NOT NULL,
            title VARCHAR(150) NOT NULL,
            message TEXT NOT NULL,
            severity VARCHAR(20) DEFAULT 'info',
            audience VARCHAR(20) NOT NULL DEFAULT 'all', -- all|admins|students|user|program
            target_user_id INT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            target_program VARCHAR(100),
            actionable JSONB,
            expires_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_notifications_audience ON notifications(audience);
        CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_notifications_target_user ON notifications(target_user_id);
    """,
    "user_notifications": """
        CREATE TABLE IF NOT EXISTS user_notifications (
            id SERIAL PRIMARY KEY,
            notification_id INT NOT NULL REFERENCES notifications(notification_id) ON DELETE CASCADE,
            user_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            is_read BOOLEAN DEFAULT FALSE,
            read_at TIMESTAMP WITH TIME ZONE,
            delivered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(notification_id, user_id)
        );
        CREATE INDEX IF NOT EXISTS idx_user_notifications_user_read ON user_notifications(user_id, is_read);
    """,
    "assessments": """
        CREATE TABLE IF NOT EXISTS assessments (
            assessment_id SERIAL PRIMARY KEY,
            course_id INT NOT NULL REFERENCES courses(course_id) ON DELETE CASCADE,
            assessment_name VARCHAR(100) NOT NULL,
            max_score INT NOT NULL,
            weight DECIMAL(5,2) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(course_id, assessment_name)
        );
    """,
    "grades": """
        CREATE TABLE IF NOT EXISTS grades (
            grade_id SERIAL PRIMARY KEY,
            student_id INT NOT NULL REFERENCES student_profiles(student_id) ON DELETE CASCADE,
            course_id INT NOT NULL REFERENCES courses(course_id) ON DELETE CASCADE,
            semester_id INT NOT NULL REFERENCES semesters(semester_id) ON DELETE CASCADE,
            score DECIMAL(5,2) NOT NULL,
            grade VARCHAR(2), -- e.g., A, B+, C
            grade_point DECIMAL(3,2),
            academic_year VARCHAR(20),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(student_id, course_id, semester_id) -- A student can only have one grade per course per semester
        );
    """
}

def create_tables_if_not_exist(conn):
    """Create all necessary tables if they don't exist."""
    for table_name in TABLES.keys():
        create_table(conn, table_name)

# =============================
# ASSESSMENT HELPERS
# =============================

def ensure_assessment(conn, course_id, assessment_name, max_score, weight):
    """Ensure an assessment exists (course_id + assessment_name uniqueness). Returns assessment_id or None."""
    if conn is None: return None
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO assessments (course_id, assessment_name, max_score, weight)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (course_id, assessment_name) DO UPDATE SET max_score = EXCLUDED.max_score, weight = EXCLUDED.weight
                RETURNING assessment_id;
                """,
                (course_id, assessment_name, max_score, weight)
            )
            aid = cursor.fetchone()[0]
            conn.commit()
            return aid
    except Exception as e:
        logger.debug(f"Assessment ensure failed for course {course_id} {assessment_name}: {e}")
        conn.rollback()
        return None

# =============================
# ASSESSMENT CRUD / FETCH HELPERS FOR API (module level)
# =============================

def fetch_assessments(conn, course_code=None):
    """Fetch assessments. If course_code provided, filter by that course.
    Returns list of dict rows with assessment and course context."""
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if course_code:
                cur.execute(
                    """
                    SELECT a.assessment_id, a.assessment_name, a.max_score, a.weight,
                           c.course_id, c.course_code, c.course_title
                    FROM assessments a
                    JOIN courses c ON a.course_id = c.course_id
                    WHERE c.course_code = %s
                    ORDER BY c.course_code, a.assessment_id
                    """,
                    (course_code,)
                )
            else:
                cur.execute(
                    """
                    SELECT a.assessment_id, a.assessment_name, a.max_score, a.weight,
                           c.course_id, c.course_code, c.course_title
                    FROM assessments a
                    JOIN courses c ON a.course_id = c.course_id
                    ORDER BY c.course_code, a.assessment_id
                    """
                )
            return cur.fetchall()
    except Exception as e:
        logger.error(f"Error fetching assessments: {e}")
        return []

def create_assessment(conn, course_code, assessment_name, max_score, weight):
    """Create or upsert an assessment for a course by code. Returns assessment_id or None."""
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT course_id FROM courses WHERE course_code=%s", (course_code,))
            row = cur.fetchone()
            if not row:
                raise ValueError(f"Course code {course_code} not found")
            return ensure_assessment(conn, row['course_id'], assessment_name, max_score, weight)
    except Exception as e:
        logger.error(f"Error creating assessment: {e}")
        return None

def update_assessment(conn, assessment_id, **fields):
    """Update assessment fields (assessment_name, max_score, weight). Returns bool success."""
    allowed = {k: v for k, v in fields.items() if k in ['assessment_name', 'max_score', 'weight'] and v is not None}
    if not allowed:
        return False
    sets = []
    params = []
    for k, v in allowed.items():
        sets.append(f"{k} = %s")
        params.append(v)
    params.append(assessment_id)
    sql = f"UPDATE assessments SET {', '.join(sets)} WHERE assessment_id = %s"
    try:
        with conn.cursor() as cur:
            cur.execute(sql, tuple(params))
            updated = cur.rowcount
        return updated > 0
    except Exception as e:
        logger.error(f"Error updating assessment {assessment_id}: {e}")
        return False

def delete_assessment(conn, assessment_id):
    """Delete an assessment by id. Returns bool success."""
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM assessments WHERE assessment_id = %s", (assessment_id,))
            deleted = cur.rowcount
        return deleted > 0
    except Exception as e:
        logger.error(f"Error deleting assessment {assessment_id}: {e}")
        return False

# =============================
# NOTIFICATION CRUD OPERATIONS
# =============================

def insert_notification(conn, type_, title, message, severity='info', audience='all', target_user_id=None, target_program=None, actionable=None, expires_at=None):
    if conn is None: return None
    # Suppression flag: Skip creating notifications if seeding or other bulk ops requested silence
    if os.getenv("SUPPRESS_SEED_NOTIFICATIONS"):
        logger.debug(f"[NOTIFY-SUPPRESSED] type={type_} title={title}")
        return None
    try:
        with conn.cursor() as cursor:
            if actionable is not None:
                cursor.execute(
                    """
                    INSERT INTO notifications (type, title, message, severity, audience, target_user_id, target_program, actionable, expires_at)
                    VALUES (%s,%s,%s,%s,%s,%s,%s, %s::json, %s)
                    RETURNING notification_id;
                    """,
                    (type_, title, message, severity, audience, target_user_id, target_program, actionable, expires_at)
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO notifications (type, title, message, severity, audience, target_user_id, target_program, actionable, expires_at)
                    VALUES (%s,%s,%s,%s,%s,%s,%s, NULL, %s)
                    RETURNING notification_id;
                    """,
                    (type_, title, message, severity, audience, target_user_id, target_program, expires_at)
                )
            nid = cursor.fetchone()[0]
            conn.commit()
            logger.info(f"Notification {nid} created (type={type_}, audience={audience})")
            return nid
    except Exception as e:
        logger.error(f"Error inserting notification: {e}")
        conn.rollback()
        return None

def _expand_audience_user_ids(conn, audience, target_user_id=None, target_program=None):
    if conn is None: return []
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            if audience == 'all':
                cursor.execute("SELECT user_id FROM users")
            elif audience == 'admins':
                cursor.execute("SELECT user_id FROM users WHERE role = 'admin'")
            elif audience == 'students':
                cursor.execute("SELECT user_id FROM users WHERE role = 'student'")
            elif audience == 'user' and target_user_id:
                cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (target_user_id,))
            else:
                # program audience reserved for later when program is linked to users
                return []
            rows = cursor.fetchall()
            return [r['user_id'] for r in rows]
    except Exception as e:
        logger.error(f"Error expanding audience {audience}: {e}")
        return []

def create_user_notification_links(conn, notification_id, user_ids):
    if conn is None: return 0
    if not user_ids: return 0
    try:
        with conn.cursor() as cursor:
            for uid in user_ids:
                try:
                    cursor.execute(
                        """
                        INSERT INTO user_notifications (notification_id, user_id)
                        VALUES (%s, %s) ON CONFLICT DO NOTHING;
                        """,
                        (notification_id, uid)
                    )
                except Exception as inner_e:
                    logger.warning(f"Skipping user {uid} link for notification {notification_id}: {inner_e}")
            conn.commit()
            return len(user_ids)
    except Exception as e:
        logger.error(f"Error creating user notification links: {e}")
        conn.rollback()
        return 0

def fetch_user_notifications(conn, user_id, unread_only=False, limit=20, before_id=None):
    if conn is None: return []
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            conditions = ["un.user_id = %s"]
            params = [user_id]
            if unread_only:
                conditions.append("un.is_read = FALSE")
            if before_id:
                conditions.append("un.id < %s")
                params.append(before_id)
            where_clause = " AND ".join(conditions)
            query = f"""
                SELECT un.id as user_notification_id, un.is_read, un.read_at, n.notification_id, n.type, n.title, n.message,
                       n.severity, n.audience, n.created_at
                FROM user_notifications un
                JOIN notifications n ON un.notification_id = n.notification_id
                WHERE {where_clause}
                ORDER BY un.id DESC
                LIMIT %s;
            """
            params.append(limit)
            cursor.execute(query, tuple(params))
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error fetching notifications for user {user_id}: {e}")
        return []

def mark_notification_read(conn, user_id, user_notification_id):
    if conn is None: return False
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE user_notifications SET is_read = TRUE, read_at = CURRENT_TIMESTAMP
                WHERE id = %s AND user_id = %s AND is_read = FALSE;
                """,
                (user_notification_id, user_id)
            )
            changed = cursor.rowcount
            if changed:
                conn.commit()
            return changed > 0
    except Exception as e:
        logger.error(f"Error marking notification {user_notification_id} read for user {user_id}: {e}")
        conn.rollback()
        return False

def mark_all_notifications_read(conn, user_id):
    if conn is None: return 0
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE user_notifications SET is_read = TRUE, read_at = CURRENT_TIMESTAMP
                WHERE user_id = %s AND is_read = FALSE;
                """,
                (user_id,)
            )
            changed = cursor.rowcount
            if changed:
                conn.commit()
            return changed
    except Exception as e:
        logger.error(f"Error marking all notifications read for user {user_id}: {e}")
        conn.rollback()
        return 0

def count_unread_notifications(conn, user_id):
    if conn is None: return 0
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM user_notifications WHERE user_id = %s AND is_read = FALSE;",
                (user_id,)
            )
            return cursor.fetchone()[0]
    except Exception as e:
        logger.error(f"Error counting unread notifications for user {user_id}: {e}")
        return 0

# --- STUDENT PROFILE CRUD OPERATIONS ---
def insert_student_profile(conn, index_number, full_name, dob, gender, contact_email=None, contact_phone=None, program=None, year_of_study=None):
    """Insert a new student profile into the student_profiles table."""
    if conn is None: return False
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO student_profiles (index_number, full_name, dob, gender, contact_email, contact_phone, program, year_of_study)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING student_id;
            """, (index_number, full_name, dob, gender, contact_email, contact_phone, program, year_of_study))
            student_id = cursor.fetchone()[0]
            conn.commit()
            logger.info(f"Student profile '{full_name}' ({index_number}) inserted with ID: {student_id}")
            return student_id
    except psycopg2.errors.UniqueViolation:
        logger.warning(f"Student with index number {index_number} already exists.")
        conn.rollback()
        return False
    except Exception as e:
        logger.error(f"Error inserting student profile {index_number}: {e}")
        conn.rollback()
        return False

def fetch_student_by_index_number(conn, index_number):
    """Fetch a student's profile and their grades by index number."""
    if conn is None: return None
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Fetch student profile
            cursor.execute("""
                SELECT * FROM student_profiles WHERE index_number = %s;
            """, (index_number,))
            student_profile = cursor.fetchone()

            if student_profile:
                # Fetch student's grades along with course and semester info
                cursor.execute("""
                    SELECT
                        g.grade_id, g.score, g.grade, g.grade_point, g.academic_year,
                        c.course_code, c.course_title, c.credit_hours,
                        s.semester_name
                    FROM grades g
                    JOIN courses c ON g.course_id = c.course_id
                    JOIN semesters s ON g.semester_id = s.semester_id
                    WHERE g.student_id = %s
                    ORDER BY s.academic_year, s.start_date, c.course_code;
                """, (student_profile['student_id'],))
                grades = cursor.fetchall()
                student_profile['grades'] = grades # Add grades list to profile
            
            return student_profile
    except Exception as e:
        logger.error(f"Error fetching student by index number {index_number}: {e}")
        return None

def fetch_all_records(conn):
    """
    Fetch all student profiles, courses, semesters, and grades from the database.
    """
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Fetch all student profiles
            cursor.execute("SELECT * FROM student_profiles ORDER BY full_name")
            students = cursor.fetchall()

            # Fetch all courses
            cursor.execute("SELECT * FROM courses ORDER BY course_code")
            courses = cursor.fetchall()

            # Fetch all semesters
            cursor.execute("SELECT * FROM semesters ORDER BY academic_year DESC, start_date DESC")
            semesters = cursor.fetchall()

            # Fetch all grades with student, course and semester information
            cursor.execute("""
                SELECT 
                    g.grade_id, g.score, g.grade, g.grade_point, g.academic_year,
                    sp.index_number, sp.full_name,
                    c.course_code, c.course_title,
                    s.semester_name
                FROM grades g
                JOIN student_profiles sp ON g.student_id = sp.student_id
                JOIN courses c ON g.course_id = c.course_id
                JOIN semesters s ON g.semester_id = s.semester_id
                ORDER BY sp.index_number, s.academic_year DESC, s.semester_name, c.course_code
            """)
            grades = cursor.fetchall()

            return {
                "students": students,
                "courses": courses,
                "semesters": semesters,
                "grades": grades
            }
    except Exception as e:
        logger.error(f"Error fetching all records: {e}")
        return None

def update_student_profile(conn, student_id, updates):
    """Update a student's profile."""
    if conn is None: return False
    if not updates:
        return True # No updates provided, still considered successful
    
    query_parts = []
    values = []
    for key, value in updates.items():
        if key in ['full_name', 'dob', 'gender', 'contact_email', 'contact_phone', 'program', 'year_of_study']:
            query_parts.append(f"{key} = %s")
            values.append(value)
        else:
            logger.warning(f"Attempted to update invalid field: {key}")

    if not query_parts:
        return True # No valid updates provided
    
    values.append(student_id)
    query = f"UPDATE student_profiles SET {', '.join(query_parts)}, updated_at = CURRENT_TIMESTAMP WHERE student_id = %s;"
    
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, tuple(values))
            if cursor.rowcount > 0:
                conn.commit()
                logger.info(f"Student profile {student_id} updated successfully.")
                return True
            else:
                logger.warning(f"No student found with ID {student_id} for update.")
                return False
    except Exception as e:
        logger.error(f"Error updating student profile {student_id}: {e}")
        conn.rollback()
        return False

def delete_student_profile(conn, student_id):
    """Delete a student profile and cascading records by student_id."""
    if conn is None: return False
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM student_profiles WHERE student_id = %s;", (student_id,))
            if cursor.rowcount > 0:
                conn.commit()
                logger.info(f"Student profile {student_id} and associated records deleted successfully.")
                return True
            else:
                logger.warning(f"No student found with ID {student_id} for deletion.")
                return False
    except Exception as e:
        logger.error(f"Error deleting student profile {student_id}: {e}")
        conn.rollback()
        return False

# --- COURSE CRUD OPERATIONS ---
def insert_course(conn, course_code, course_title, credit_hours):
    """Insert a new course."""
    if conn is None: return False
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO courses (course_code, course_title, credit_hours)
                VALUES (%s, %s, %s) RETURNING course_id;
            """, (course_code, course_title, credit_hours))
            course_id = cursor.fetchone()[0]
            conn.commit()
            logger.info(f"Course '{course_code}' inserted with ID: {course_id}")
            # Notification: new course (guarded by suppression in insert_notification)
            try:
                nid = insert_notification(conn, 'new_course', 'New Course Added', f"Course {course_code} - {course_title} created", 'info', 'admins')
                if nid:
                    user_ids = _expand_audience_user_ids(conn, 'admins')
                    create_user_notification_links(conn, nid, user_ids)
            except Exception as notify_err:
                logger.warning(f"Failed to create new_course notification: {notify_err}")
            return course_id
    except psycopg2.errors.UniqueViolation:
        logger.warning(f"Course with code {course_code} already exists.")
        conn.rollback()
        return False
    except Exception as e:
        logger.error(f"Error inserting course {course_code}: {e}")
        conn.rollback()
        return False

def fetch_all_courses(conn):
    """Fetch all courses."""
    if conn is None: return []
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM courses ORDER BY course_code;")
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error fetching all courses: {e}")
        return []

def fetch_course_by_code(conn, course_code):
    """Fetch a single course by its code."""
    if conn is None: return None
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM courses WHERE course_code = %s;", (course_code,))
            return cursor.fetchone()
    except Exception as e:
        logger.error(f"Error fetching course by code {course_code}: {e}")
        return None

def update_course(conn, course_id, updates):
    """Update an existing course."""
    if conn is None: return False
    if not updates:
        return True
    
    query_parts = []
    values = []
    for key, value in updates.items():
        if key in ['course_title', 'credit_hours']:
            query_parts.append(f"{key} = %s")
            values.append(value)
        else:
            logger.warning(f"Attempted to update invalid course field: {key}")
            
    if not query_parts:
        return True # No valid updates provided

    values.append(course_id)
    query = f"UPDATE courses SET {', '.join(query_parts)} WHERE course_id = %s;"

    try:
        with conn.cursor() as cursor:
            cursor.execute(query, tuple(values))
            if cursor.rowcount > 0:
                conn.commit()
                logger.info(f"Course {course_id} updated successfully.")
                return True
            else:
                logger.warning(f"No course found with ID {course_id} for update.")
                return False
    except Exception as e:
        logger.error(f"Error updating course {course_id}: {e}")
        conn.rollback()
        return False

def delete_course(conn, course_id):
    """Delete a course by its ID."""
    if conn is None: return False
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM courses WHERE course_id = %s;", (course_id,))
            if cursor.rowcount > 0:
                conn.commit()
                logger.info(f"Course {course_id} deleted successfully.")
                return True
            else:
                logger.warning(f"No course found with ID {course_id} for deletion.")
                return False
    except Exception as e:
        logger.error(f"Error deleting course {course_id}: {e}")
        conn.rollback()
        return False

# --- SEMESTER CRUD OPERATIONS ---
def insert_semester(conn, semester_name, start_date, end_date, academic_year=None):
    """Insert a new semester."""
    if conn is None: return False
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO semesters (semester_name, academic_year, start_date, end_date)
                VALUES (%s, %s, %s, %s) RETURNING semester_id;
            """, (semester_name, academic_year, start_date, end_date))
            semester_id = cursor.fetchone()[0]
            conn.commit()
            logger.info(f"Semester '{semester_name}' inserted with ID: {semester_id}")
            # Notification: new semester (guarded by suppression in insert_notification)
            try:
                nid = insert_notification(conn, 'new_semester', 'New Semester Created', f"Semester {semester_name} ({academic_year or ''}) added", 'info', 'admins')
                if nid:
                    user_ids = _expand_audience_user_ids(conn, 'admins')
                    create_user_notification_links(conn, nid, user_ids)
            except Exception as notify_err:
                logger.warning(f"Failed to create new_semester notification: {notify_err}")
            return semester_id
    except psycopg2.errors.UniqueViolation:
        logger.warning(f"Semester with name {semester_name} already exists.")
        conn.rollback()
        return False
    except Exception as e:
        logger.error(f"Error inserting semester {semester_name}: {e}")
        conn.rollback()
        return False

def fetch_all_semesters(conn):
    """Fetch all semesters."""
    if conn is None: return []
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM semesters ORDER BY start_date DESC;")
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error fetching all semesters: {e}")
        return []

def fetch_semester_by_name(conn, semester_name):
    """Fetch a single semester by its name."""
    if conn is None: return None
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM semesters WHERE semester_name = %s;", (semester_name,))
            return cursor.fetchone()
    except Exception as e:
        logger.error(f"Error fetching semester by name {semester_name}: {e}")
        return None

def fetch_current_semester(conn):
    """Fetch the currently active semester."""
    if conn is None: return None
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM semesters WHERE is_current = TRUE;")
            return cursor.fetchone()
    except Exception as e:
        logger.error(f"Error fetching current semester: {e}")
        return None

def set_current_semester(conn, semester_id):
    """Set a specific semester as the current active one, and unmark others."""
    if conn is None: return False
    try:
        with conn.cursor() as cursor:
            # Start a transaction
            conn.autocommit = False # Disable autocommit for explicit transaction control

            # 1. Unset all current semesters
            cursor.execute("UPDATE semesters SET is_current = FALSE WHERE is_current = TRUE;")
            logger.info("All previous current semesters unset.")

            # 2. Set the specified semester as current
            cursor.execute("UPDATE semesters SET is_current = TRUE WHERE semester_id = %s RETURNING semester_id;", (semester_id,))
            updated_id = cursor.fetchone()
            
            if updated_id:
                conn.commit()
                logger.info(f"Semester {semester_id} successfully set as current.")
                # Notification: current semester changed (guarded by suppression)
                try:
                    nid = insert_notification(conn, 'semester_change', 'Current Semester Updated', f"Semester ID {semester_id} is now current", 'info', 'admins')
                    if nid:
                        user_ids = _expand_audience_user_ids(conn, 'admins')
                        create_user_notification_links(conn, nid, user_ids)
                except Exception as notify_err:
                    logger.warning(f"Failed to create semester_change notification: {notify_err}")
                return True
            else:
                conn.rollback() # Rollback if no semester was updated (e.g., ID not found)
                logger.warning(f"Failed to set semester {semester_id} as current; ID not found.")
                return False
    except Exception as e:
        logger.error(f"Error setting current semester {semester_id}: {e}")
        conn.rollback() # Rollback on any error
        return False
    finally:
        conn.autocommit = True # Re-enable autocommit
        
def update_semester(conn, semester_id, updates):
    """Update an existing semester."""
    if conn is None: return False
    if not updates:
        return True # No updates provided, still considered successful
    
    query_parts = []
    values = []
    for key, value in updates.items():
        if key in ['semester_name', 'academic_year', 'start_date', 'end_date', 'is_current']: # Added academic_year
            query_parts.append(f"{key} = %s")
            values.append(value)
        else:
            logger.warning(f"Attempted to update invalid semester field: {key}")

    if not query_parts:
        return True # No valid updates provided
            
    values.append(semester_id)
    query = f"UPDATE semesters SET {', '.join(query_parts)} WHERE semester_id = %s;"
    
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, tuple(values))
                
            if cursor.rowcount > 0:
                conn.commit()
                logger.info(f"Semester {semester_id} updated successfully")
                return True
            else:
                logger.warning(f"No semester found with ID {semester_id} for update.")
                return False
    except Exception as e:
        logger.error(f"Error updating semester {semester_id}: {e}")
        conn.rollback()
        return False

def delete_semester(conn, semester_id):
    """Delete a semester from the system."""
    if conn is None: return False
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM semesters WHERE semester_id = %s", (semester_id,))
            
            if cursor.rowcount > 0:
                conn.commit()
                logger.info(f"Semester {semester_id} deleted successfully.")
                return True
            else:
                logger.warning(f"No semester found with ID {semester_id} for deletion.")
                return False
    except Exception as e:
        logger.error(f"Error deleting semester {semester_id}: {e}")
        conn.rollback()
        return False

# --- GRADE CRUD OPERATIONS ---
def insert_grade(conn, student_id, course_id, semester_id, score, grade, grade_point, academic_year):
    """Insert a student's grade for a specific course and semester."""
    if conn is None: return False
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO grades (student_id, course_id, semester_id, score, grade, grade_point, academic_year)
                VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING grade_id;
            """, (student_id, course_id, semester_id, score, grade, grade_point, academic_year))
            grade_id = cursor.fetchone()[0]
            conn.commit()
            logger.info(f"Grade inserted for student {student_id}, course {course_id}, semester {semester_id} with ID: {grade_id}")
            # Notification: grade inserted (guarded by suppression)
            try:
                nid = insert_notification(conn, 'grade_entry', 'Grade Recorded', f"Grade recorded for student {student_id} course {course_id}", 'info', 'admins')
                if nid:
                    user_ids = _expand_audience_user_ids(conn, 'admins')
                    create_user_notification_links(conn, nid, user_ids)
            except Exception as notify_err:
                logger.warning(f"Failed to create grade_entry notification: {notify_err}")
            return grade_id
    except psycopg2.errors.UniqueViolation:
        logger.warning(f"Grade already exists for student {student_id} in course {course_id} for semester {semester_id}.")
        conn.rollback()
        return False
    except Exception as e:
        logger.error(f"Error inserting grade for student {student_id}: {e}")
        conn.rollback()
        return False

def fetch_grades_by_index_number(conn, index_number):
    """Fetch all grades for a given student index number."""
    if conn is None: return []
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT
                    g.grade_id, g.score, g.grade, g.grade_point, g.academic_year,
                    c.course_code, c.course_title, c.credit_hours,
                    s.semester_name, s.start_date, s.end_date
                FROM grades g
                JOIN student_profiles sp ON g.student_id = sp.student_id
                JOIN courses c ON g.course_id = c.course_id
                JOIN semesters s ON g.semester_id = s.semester_id
                WHERE sp.index_number = %s
                ORDER BY s.academic_year, s.start_date, c.course_code;
            """, (index_number,))
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error fetching grades for student {index_number}: {e}")
        return []

def update_student_score(conn, student_id, course_id, semester_id, new_score, new_grade, new_grade_point, academic_year):
    """Update a student's score for a specific course and semester using IDs."""
    if conn is None: return False
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE grades
                SET score = %s, grade = %s, grade_point = %s, academic_year = %s, updated_at = CURRENT_TIMESTAMP
                WHERE student_id = %s
                AND course_id = %s
                AND semester_id = %s
                RETURNING grade_id;
            """, (new_score, new_grade, new_grade_point, academic_year, student_id, course_id, semester_id))
            
            if cursor.rowcount > 0:
                conn.commit()
                logger.info(f"Score for student_id {student_id} in course_id {course_id} (semester_id {semester_id}) updated to {new_score}.")
                # Notification: grade updated (guarded by suppression)
                try:
                    nid = insert_notification(conn, 'grade_update', 'Grade Updated', f"Updated score for student {student_id} course {course_id}", 'info', 'admins')
                    if nid:
                        user_ids = _expand_audience_user_ids(conn, 'admins')
                        create_user_notification_links(conn, nid, user_ids)
                except Exception as notify_err:
                    logger.warning(f"Failed to create grade_update notification: {notify_err}")
                return True
            else:
                logger.warning(f"Could not find matching grade to update for student_id {student_id}, course_id {course_id}, semester_id {semester_id}.")
                return False
    except Exception as e:
        logger.error(f"Error updating score for student_id {student_id}, course_id {course_id}, semester_id {semester_id}: {e}")
        conn.rollback()
        return False

def insert_complete_student_record(conn, student_profile_data, grade_data):
    """
    Inserts a student profile and their grade(s) in a single transactional operation.
    Rolls back if any part fails.
    """
    if conn is None: return False
    try:
        # Disable autocommit to manage transaction manually
        conn.autocommit = False 

        # 1. Insert/Get Student Profile
        student_profile_from_db = fetch_student_by_index_number(conn, student_profile_data['index_number'])
        if student_profile_from_db:
            student_id = student_profile_from_db['student_id']
            logger.info(f"Student {student_profile_data['index_number']} already exists with ID: {student_id}. Skipping profile insertion.")
            # Optionally update existing profile if needed, but for now, just use its ID
        else:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO student_profiles (index_number, full_name, dob, gender, contact_email, contact_phone, program, year_of_study)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING student_id;
                """, (
                    student_profile_data['index_number'],
                    student_profile_data['name'], # Assuming 'name' in student_profile_data maps to 'full_name'
                    student_profile_data.get('dob'),
                    student_profile_data.get('gender'),
                    student_profile_data.get('contact_email'),
                    student_profile_data.get('contact_phone'),
                    student_profile_data.get('program'),
                    student_profile_data.get('year_of_study')
                ))
                student_id = cursor.fetchone()[0]
                logger.info(f"Student profile '{student_profile_data['name']}' ({student_profile_data['index_number']}) inserted with ID: {student_id}")

        # 2. Insert Grade(s)
        if grade_data:
            for grade in grade_data:
                # Resolve course_id and semester_id
                course = fetch_course_by_code(conn, grade['course_code'])
                if not course:
                    raise ValueError(f"Course with code {grade['course_code']} not found for bulk import.")
                course_id = course['course_id']

                semester_obj = fetch_semester_by_name(conn, grade['semester_name'])
                if not semester_obj:
                    raise ValueError(f"Semester with name {grade['semester_name']} not found for bulk import.")
                semester_id = semester_obj['semester_id']

                # Calculate grade and grade point
                calculated_grade = calculate_grade(grade['score'])
                calculated_grade_point = get_grade_point(grade['score'])

                # Use the helper function to insert/update grade
                insert_grade(conn, student_id, course_id, semester_id, grade['score'], 
                             calculated_grade, calculated_grade_point, grade['academic_year'])

        # Commit transaction
        conn.commit()
        logger.info(f"Transaction completed for student {student_profile_data['index_number']}.")
        return True

    except Exception as e:
        logger.error(f"Transaction failed for student {student_profile_data['index_number']}: {e}")
        conn.rollback()
        return False

    finally:
        conn.autocommit = True # Re-enable autocommit

# --- AUTHENTICATION OPERATIONS (from auth.py, simplified for db context) ---
def get_user_by_username(conn, username):
    """Fetch user by username."""
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM users WHERE username = %s;", (username,))
            return cursor.fetchone()
    except Exception as e:
        logger.error(f"Error fetching user by username {username}: {e}")
        return None

def create_user(conn, username, password_hash, role):
    """Create a new user in the database."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO users (username, password, role)
                VALUES (%s, %s, %s) RETURNING user_id;
            """, (username, password_hash, role))
            user_id = cursor.fetchone()[0]
            conn.commit()
            logger.info(f"User '{username}' created with ID: {user_id}")
            return user_id
    except psycopg2.errors.UniqueViolation:
        logger.warning(f"User with username {username} already exists.")
        conn.rollback()
        return False
    except Exception as e:
        logger.error(f"Error creating user {username}: {e}")
        conn.rollback()
        return False

def update_user_password(conn, user_id, new_password_hash):
    """Update a user's password."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE users SET password = %s WHERE user_id = %s;
            """, (new_password_hash, user_id))
            if cursor.rowcount > 0:
                conn.commit()
                logger.info(f"Password for user {user_id} updated successfully.")
                return True
            return False
    except Exception as e:
        logger.error(f"Error updating password for user {user_id}: {e}")
        conn.rollback()
        return False

