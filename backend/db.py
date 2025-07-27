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
            cursor.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'student';")
            conn.commit()
        except Exception:
            conn.rollback()  # Ignore if column already exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL
            );
        """)
        conn.commit()  # Commit the changes to the database
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        conn.rollback()  # Rollback in case of error
    finally:
        cursor.close()

def insert_student_record(conn, student):
    """
    inserts a single student record into the database.
    expects a connection object and a student dictionary with index, number, full_name, course, score and grade.
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
            logger.info(f"Inserted student record: {student['index_number']}")
    except Exception as e:
        logger.error(f"Error inserting student record {student['index_number']}: {e}")
        conn.rollback()

def fetch_all_records():
    """
    fetches all student records from the database.
    returns a list of dictionaries, eaxh repesenting a student record.
    """

    conn = connect_to_db()
    if conn is None:
        logger.error("Failed to connect to the database. Cannot fetch records.")
        return []
    logger.info(f"[fetch_all_records] Connected to database with params: dbname={DB_NAME}, user={DB_USER}, host={DB_HOST}, port={DB_PORT}")
    cur = conn.cursor()
    try:
        cur.execute("SELECT index_number, full_name, course, score, grade FROM student_results;")
        rows  = cur.fetchall() # returns all rows as a list of tuples
        logger.info(f"[fetch_all_records] Number of rows fetched: {len(rows)}")
        results = []
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