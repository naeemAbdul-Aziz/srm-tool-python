# auth.py
# Authentication and user management module
import hashlib
import getpass
from db import connect_to_db

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, password, role):
    conn = connect_to_db()
    if conn is None:
        print("Error: Could not connect to database.")
        return False
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO users (username, password, role)
                VALUES (%s, %s, %s)
            """, (username, hash_password(password), role))
            conn.commit()
        return True
    except Exception as e:
        print(f"Error creating user: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def authenticate_user(username, password):
    conn = connect_to_db()
    if conn is None:
        print("Error: Could not connect to database.")
        return None
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT password, role FROM users WHERE username = %s", (username,))
            result = cur.fetchone()
            if result and result[0] == hash_password(password):
                return result[1]  # Return role
            else:
                return None
    except Exception as e:
        print(f"Error authenticating user: {e}")
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
            print("Error: Could not connect to database.")
            return False
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM student_results WHERE index_number = %s", (username,))
                exists = cur.fetchone()
                if not exists:
                    print("Index number not found in student records. Please contact admin.")
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
# auth.py
# Authentication and user management module
