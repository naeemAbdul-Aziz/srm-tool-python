# db.py
# Database connection and operations module
import psycopg2
from config import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT
from logger import get_logger

logger = get_logger(__name__)

def connect_to_db():
    """Establish a connection to the PostgreSQL database."""
    try:
        logger.info(f"Connecting to database with params: dbname={DB_NAME}, user={DB_USER}, host={DB_HOST}, port={DB_PORT}")
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        return conn  # Return the database connection object
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        return None
    
def create_tables(conn):
    """Create the students table in the database if it doesn't exist."""
    cursor = conn.cursor()
    if conn is None:
        logger.error("Failed to connect to the database. Tables cannot be created.")
        return
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS student_results (
                id SERIAL PRIMARY KEY,
                index_number VARCHAR(10) NOT NULL UNIQUE,
                full_name TEXT NOT NULL,
                course TEXT NOT NULL,
                score INTEGER NOT NULL CHECK (score >= 0 AND score <= 100),
                grade CHAR(1)
            );
        """)
        # Try to add 'role' column if it doesn't exist (migration for legacy table)
        try:
            # Check if column exists before adding
            cursor.execute("SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='role';")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'student';")
                logger.info("Added 'role' column to 'users' table.")
            else:
                logger.info("'role' column already exists in 'users' table.")
            conn.commit()
        except Exception as e:
            logger.warning(f"Could not add 'role' column to 'users' table (might already exist or other error): {e}")
            conn.rollback()  # Rollback if ALTER TABLE fails
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL
            );
        """)
        conn.commit()  # Commit the changes to the database
        logger.info("Tables checked/created successfully.")
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        conn.rollback()  # Rollback in case of error
    finally:
        cursor.close()

def insert_student_record(conn, student):
    """
    Inserts a single student record into the database.
    Expects a connection object and a student dictionary with index, number, full_name, course, score and grade.
    """
    try:
        with conn.cursor() as cur:
            query = """
                INSERT INTO student_results (index_number, full_name, course, score, grade)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (index_number) DO UPDATE SET
                    full_name = EXCLUDED.full_name,
                    course = EXCLUDED.course,
                    score = EXCLUDED.score,
                    grade = EXCLUDED.grade;
            """
            cur.execute(query, (
                student['index_number'],
                student['full_name'],
                student['course'],
                student['score'],
                student['grade']
            ))
            conn.commit()
            logger.info(f"Inserted/Updated student record: {student['index_number']}")
            return True # Indicate success
    except Exception as e:
        logger.error(f"Error inserting/updating student record {student['index_number']}: {e}")
        conn.rollback()
        return False # Indicate failure

def fetch_all_records():
    """
    Fetches all student records from the database.
    Returns a list of dictionaries, each representing a student record.
    """
    conn = connect_to_db()
    if conn is None:
        logger.error("Failed to connect to the database. Cannot fetch records.")
        return []
    logger.info(f"[fetch_all_records] Connected to database with params: dbname={DB_NAME}, user={DB_USER}, host={DB_HOST}, port={DB_PORT}")
    cur = conn.cursor()
    results = []
    try:
        cur.execute("SELECT index_number, full_name, course, score, grade FROM student_results;")
        rows  = cur.fetchall() # returns all rows as a list of tuples
        logger.info(f"[fetch_all_records] Number of rows fetched: {len(rows)}")
        for row in rows:
            results.append({
                'index_number': row[0],
                'full_name': row[1],
                'course': row[2],
                'score': row[3],
                'grade': row[4]
            })
        logger.info(f"Fetched {len(results)} records from the database.")
    except Exception as e:
        logger.error(f"Error fetching records: {e}")
    finally:
        cur.close()
        conn.close()
    return results

def fetch_student_by_index_number(index_number):
    """
    Fetches a single student record by index number from the database.
    Returns a dictionary if found, None otherwise.
    """
    conn = connect_to_db()
    if conn is None:
        logger.error("Failed to connect to the database. Cannot fetch record by index number.")
        return None
    cur = conn.cursor()
    student_record = None
    try:
        cur.execute("SELECT index_number, full_name, course, score, grade FROM student_results WHERE index_number = %s;", (index_number,))
        row = cur.fetchone()
        if row:
            student_record = {
                'index_number': row[0],
                'full_name': row[1],
                'course': row[2],
                'score': row[3],
                'grade': row[4]
            }
            logger.info(f"Fetched record for index number: {index_number}")
        else:
            logger.info(f"No record found for index number: {index_number}")
    except Exception as e:
        logger.error(f"Error fetching record for index number {index_number}: {e}")
    finally:
        cur.close()
        conn.close()
    return student_record

def update_student_score(index_number, new_score, new_grade):
    """
    Updates the score and grade for a student based on their index number.
    Returns True on success, False on failure.
    """
    conn = connect_to_db()
    if conn is None:
        logger.error("Failed to connect to the database. Cannot update student score.")
        return False
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE student_results
                SET score = %s, grade = %s
                WHERE index_number = %s;
            """, (new_score, new_grade, index_number))
            conn.commit()
            if cur.rowcount > 0:
                logger.info(f"Student {index_number} score updated to {new_score}.")
                return True
            else:
                logger.warning(f"No student found with index number {index_number} to update.")
                return False
    except Exception as e:
        logger.error(f"Error updating student score for {index_number}: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()