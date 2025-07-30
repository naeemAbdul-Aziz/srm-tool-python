# auth.py - authentication and user management module with session integration

import hashlib
import getpass
from db import connect_to_db, fetch_student_by_index_number
from logger import get_logger
from session import session_manager, set_user

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
    """authenticate user and gather additional user data"""
    conn = connect_to_db()
    if conn is None:
        logger.error("error: could not connect to database for user authentication.")
        return None, None
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT password, role FROM users WHERE username = %s", (username,))
            result = cur.fetchone()
            if result and result[0] == hash_password(password):
                role = result[1]
                logger.info(f"user '{username}' authenticated successfully.")
                
                # gather additional user data based on role
                user_data = {}
                if role == 'student':
                    # get student profile and grades
                    student_info = fetch_student_by_index_number(conn, username)
                    if student_info:
                        user_data = {
                            'profile': student_info['profile'],
                            'grades': student_info['grades'],
                            'full_name': student_info['profile'].get('name', username)
                        }
                        logger.info(f"loaded student data for {username}")
                elif role == 'admin':
                    user_data = {
                        'full_name': username,
                        'admin_level': 'full_access'  # could be extended for different admin levels
                    }
                    logger.info(f"loaded admin data for {username}")
                
                return role, user_data
            else:
                logger.warning(f"authentication failed for user '{username}'.")
                return None, None
    except Exception as e:
        logger.error(f"error authenticating user '{username}': {e}")
        return None, None
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
        # check if index number exists in student_profiles table
        conn = connect_to_db()
        if conn is None:
            print("error: could not connect to database. cannot verify index number.")
            return False
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM student_profiles WHERE index_number = %s", (username,))
                exists = cur.fetchone()
                if not exists:
                    print("index number not found in student records. please contact admin.")
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
    """handle user login with session creation"""
    print("\n--- Login ---")
    role_hint = input("Are you logging in as admin or student? ").strip().lower()
    
    # guide user on what to enter as 'username' based on role
    if role_hint == "student":
        username = input("Enter your index number: ")
        if not username.isdigit() or len(username) < 5:
            print("invalid index number. must be numeric and at least 5 digits.")
            return None, None
    else:
        username = input("Username: ")
    
    password = getpass.getpass("Password: ")
    role, user_data = authenticate_user(username, password)
    
    if role and user_data:
        # create session with user data
        session_id = session_manager.create_session(username, role, user_data)
        set_user(username, role)  # legacy support
        
        # display personalized welcome message
        full_name = user_data.get('full_name', username)
        print(f"login successful! welcome, {full_name} ({role})")
        
        if role == 'student' and user_data.get('grades'):
            grade_count = len(user_data['grades'])
            print(f"you have {grade_count} course grades on record.")
        elif role == 'admin':
            print("you have full administrative access.")
            
        logger.info(f"session created with id: {session_id}")
        return username, role
    else:
        print("login failed. invalid credentials.")
        return None, None

def logout():
    """handle user logout and session cleanup"""
    current_user = session_manager.get_current_user()
    if current_user:
        username = current_user['username']
        role = current_user['role']
        duration = session_manager.get_session_duration()
        
        session_manager.clear_session()
        print(f"goodbye, {username}! session lasted {duration:.1f} minutes.")
        logger.info(f"user {username} ({role}) logged out after {duration:.1f} minutes")
    else:
        print("no active session to logout from.")
        logger.warning("logout attempted with no active session")
