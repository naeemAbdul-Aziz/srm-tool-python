# auth.py
# Authentication and user management module
import hashlib
import getpass
from db import connect_to_db
from logger import get_logger # Import logger for auth file

logger = get_logger(__name__)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, password, role):
    conn = connect_to_db()
    if conn is None:
        logger.error("Error: Could not connect to database for user creation.")
        return False
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO users (username, password, role)
                VALUES (%s, %s, %s)
            """, (username, hash_password(password), role))
            conn.commit()
        logger.info(f"User '{username}' created successfully with role '{role}'.")
        return True
    except Exception as e:
        logger.error(f"Error creating user '{username}': {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def authenticate_user(username, password):
    conn = connect_to_db()
    if conn is None:
        logger.error("Error: Could not connect to database for user authentication.")
        return None
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT password, role FROM users WHERE username = %s", (username,))
            result = cur.fetchone()
            if result and result[0] == hash_password(password):
                logger.info(f"User '{username}' authenticated successfully.")
                return result[1]  # Return role
            else:
                logger.warning(f"Authentication failed for user '{username}'.")
                return None
    except Exception as e:
        logger.error(f"Error authenticating user '{username}': {e}")
        return None
    finally:
        conn.close()

def sign_up():
    print("\n--- Sign Up ---")
    role = input("Role (admin/student): ").strip().lower()
    if role not in ["admin", "student"]:
        print("Invalid role. Must be 'admin' or 'student'.")
        return False
    if role == "student":
        username = input("Enter your index number: ")
        if not username.isdigit() or len(username) < 5:
            print("Invalid index number. Must be numeric and at least 5 digits.")
            return False
        # Check if index number exists in student_results table
        conn = connect_to_db()
        if conn is None:
            print("Error: Could not connect to database. Cannot verify index number.")
            return False
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM student_results WHERE index_number = %s", (username,))
                exists = cur.fetchone()
                if not exists:
                    print("Index number not found in student records. Please contact admin.")
                    return False
        except Exception as e:
            logger.error(f"Error checking index number during sign-up: {e}")
            print("An error occurred while verifying index number.")
            return False
        finally:
            conn.close()
    else:
        username = input("Choose a username: ")
    password = getpass.getpass("Choose a password: ")
    if create_user(username, password, role):
        print("User created successfully.")
        return True
    else:
        print("Failed to create user.")
        return False

def login():
    print("\n--- Login ---")
    role_hint = input("Are you logging in as admin or student? ").strip().lower()
    # It's better to just get the username and let authenticate_user figure out the role
    # This `role_hint` is mostly for guiding the user on what to enter as 'username'
    if role_hint == "student":
        username = input("Enter your index number: ")
        if not username.isdigit() or len(username) < 5:
            print("Invalid index number. Must be numeric and at least 5 digits.")
            return None, None
    else:
        username = input("Username: ")
    password = getpass.getpass("Password: ")
    role = authenticate_user(username, password)
    if role:
        print(f"Login successful. Role: {role}")
        return username, role
    else:
        print("Login failed. Invalid credentials.")
        return None, None