# auth.py - authentication and user management module with session integration

import hashlib
import bcrypt
import getpass
# psycopg2 not directly needed here after idempotent ON CONFLICT approach
# (left commented for future specific exception handling if desired)
# import psycopg2
# from psycopg2 import errors
from db import connect_to_db, fetch_student_by_index_number # fetch_student_by_index_number now handles its own connection
from logger import get_logger
from session import session_manager, set_user # Assuming session.py exists and works as expected

logger = get_logger(__name__)

def hash_password(password):
    """Hash password using bcrypt for security."""
    # Generate a salt and hash the password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password, hashed_password):
    """Verify password against stored hash."""
    try:
        # Check if it's a legacy SHA256 hash (no $ symbols typical of bcrypt)
        if not hashed_password.startswith('$2b$'):
            # Legacy SHA256 hash - check and potentially migrate
            legacy_hash = hashlib.sha256(password.encode()).hexdigest()
            if hashed_password == legacy_hash:
                logger.warning("Legacy password hash detected. Consider updating user password.")
                return True
            return False
        
        # Verify with bcrypt
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception as e:
        logger.error(f"Error verifying password: {e}")
        return False

def create_user(username, password, role):
    """Create a user if it does not already exist.

    Returns True if inserted, False if already exists or on error.
    Duplicate username now treated as a benign condition (idempotent).
    """
    conn = connect_to_db()
    if conn is None:
        logger.error("Error: Could not connect to database for user creation.")
        return False
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (username, password, role)
                VALUES (%s, %s, %s)
                ON CONFLICT (username) DO NOTHING
                RETURNING user_id
                """,
                (username, hash_password(password), role)
            )
            inserted = cur.fetchone()
            conn.commit()
            if inserted:
                logger.info(f"User '{username}' created successfully with role '{role}'.")
                return True
            else:
                logger.debug(f"User '{username}' already exists; skipping creation.")
                return False
    except Exception as e:
    # Generic exception; ON CONFLICT DO NOTHING prevents IntegrityError bubbling
        logger.error(f"Error creating user '{username}': {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def fetch_user_data(conn, username):
    """Fetch user data from the database."""
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id, username, password, role FROM users WHERE username = %s;", (username,))
            return cur.fetchone()
    except Exception as e:
        logger.error(f"Error fetching user data for '{username}': {e}")
        return None

def authenticate_user(username, password):
    """Authenticate user and gather additional user data with optimized session handling."""
    conn = connect_to_db()
    if conn is None:
        logger.error("Error: Could not connect to database for authentication.")
        return None
    try:
        user = fetch_user_data(conn, username)

        if user and verify_password(password, user[2]): # user[2] is the hashed password
            logger.info(f"User '{username}' authenticated successfully.")
            role = user[3] # user[3] is the role

            user_data = {
                'username': username,
                'role': role
            }

            if role == 'student':
                # For students, ensure index_number is set
                user_data['index_number'] = username  # Student username IS their index number
                
                # Fetch their full profile and grades
                student_profile = fetch_student_by_index_number(conn, username)
                if student_profile:
                    user_data.update(student_profile)
                    logger.info(f"Student data loaded for {username}.")
                else:
                    logger.warning(f"No student profile found for index number: {username}. User authenticated as student, but no record.")
            elif role == 'admin':
                # For admin users, ensure admin-specific data is available
                user_data['admin_level'] = 'full'
            
            # Only create session if one doesn't already exist for this user
            current_session = session_manager.get_current_user()
            if not current_session or current_session.get('username') != username:
                # create session with user data
                session_id = session_manager.create_session(username, role, user_data)
                set_user(username, role)  # legacy support
                
                # display personalized welcome message
                full_name = user_data.get('full_name', username)
                logger.info(f"Login successful! Welcome, {full_name} ({role}).")
                
                if role == 'student' and user_data.get('grades'):
                    grade_count = len(user_data['grades'])
                    logger.info(f"You have {grade_count} course grades on record.")
                elif role == 'admin':
                    logger.info("You have full administrative access.")
                    
                logger.info(f"Session created with id: {session_id}")
            else:
                logger.debug(f"Session already exists for user {username}, reusing...")
                
            return user_data # Return the user_data dictionary
        else:
            logger.warning(f"Authentication failed for user '{username}'.")
            return None
    except Exception as e:
        logger.error(f"Error during authentication for user '{username}': {e}")
        return None
    finally:
        if conn:
            conn.close()

def logout():
    """handle user logout and session cleanup"""
    current_user = session_manager.get_current_user()
    if current_user:
        username = current_user['username']
        role = current_user['role']
        duration = session_manager.get_session_duration()
        
        session_manager.clear_session()
        logger.info(f"User {username} ({role}) logged out after {duration:.1f} minutes.")
    else:
        logger.info("Logout attempted with no active session.")

def sign_up(role='student'):
    """handle user sign-up process (for students or admins)"""
    logger.info(f"--- SIGN UP AS {role.upper()} ---")
    while True:
        username = input("Enter desired username (Index Number for Students): ").strip()
        if not username:
            logger.warning("Username cannot be empty.")
            continue
        
        # Check if username already exists in users table
        conn = connect_to_db()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT username FROM users WHERE username = %s;", (username,))
                    if cur.fetchone():
                        logger.warning("Username already taken. Please choose a different one.")
                        conn.close()
                        continue
            except Exception as e:
                logger.error(f"Error checking existing username: {e}")
                logger.error("An error occurred while checking username availability.")
                conn.close()
                return False
            finally:
                conn.close() # Ensure connection is closed

        password = getpass.getpass("Enter password: ").strip()
        if not password:
            logger.warning("Password cannot be empty.")
            continue
        
        confirm_password = getpass.getpass("Confirm password: ").strip()
        if password != confirm_password:
            logger.warning("Passwords do not match. Please try again.")
            continue
        
        # If student, ask for full name
        full_name = None
        if role == 'student':
            full_name = input("Enter your full name: ").strip()
            if not full_name:
                logger.warning("Full name cannot be empty for students.")
                continue

        # Create user in 'users' table
        if create_user(username, password, role):
            # If student, also create a student_profile entry
            if role == 'student':
                conn_profile = connect_to_db()
                if conn_profile:
                    try:
                        from db import insert_student_profile # Import here to avoid circular dependency
                        # Using username as index_number for student profile
                        # Defaulting dob/gender/contact_info for now, can be updated later via profile management
                        student_id = insert_student_profile(conn_profile, username, full_name, None, None, None, None, None, None)
                        if student_id:
                            logger.info(f"Student profile created for {username} (ID: {student_id}).")
                        else:
                            logger.error(f"Failed to create student profile for {username} after user creation.")
                            # Consider rolling back user creation if profile creation is critical
                    except Exception as e:
                        logger.error(f"Error creating student profile during sign up for {username}: {e}")
                    finally:
                        conn_profile.close()
            logger.info("Sign up successful! You can now log in.")
            return True
        else:
            logger.error("Sign up failed. Please try again later.")
            return False

def create_student_account(index_number, full_name, password=None):
    """Create a complete student account with user credentials and profile"""
    conn = connect_to_db()
    if conn is None:
        logger.error("Error: Could not connect to database for student account creation.")
        return False, None
    
    try:
        # Generate password if not provided
        if password is None:
            # Use last 4 digits of index number + "2024" as default password
            password = index_number[-4:] + "2024"
        
        # Check if user already exists
        with conn.cursor() as cur:
            cur.execute("SELECT username FROM users WHERE username = %s;", (index_number,))
            if cur.fetchone():
                logger.warning(f"User account already exists for index number: {index_number}")
                return False, "User account already exists"
        
        # Check if student profile already exists
        with conn.cursor() as cur:
            cur.execute("SELECT student_id FROM student_profiles WHERE index_number = %s;", (index_number,))
            existing_profile = cur.fetchone()
        
        student_id = None
        
        if existing_profile:
            # Profile exists, just create user account
            student_id = existing_profile[0]
            logger.info(f"Student profile already exists for {index_number}, creating user account only")
        else:
            # Create student profile first
            from db import insert_student_profile
            student_id = insert_student_profile(conn, index_number, full_name, None, None, None, None, None, None)
            
            if not student_id:
                logger.error(f"Failed to create student profile for {index_number}")
                return False, "Failed to create student profile"
            
            logger.info(f"Created student profile for {index_number} (ID: {student_id})")
        
        # Create user account
        if create_user(index_number, password, 'student'):
            logger.info(f"Student account created for {index_number} ({full_name})")
            return True, {
                'index_number': index_number,
                'full_name': full_name,
                'password': password,
                'student_id': student_id
            }
        else:
            # If profile was just created, clean it up
            if not existing_profile and student_id:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM student_profiles WHERE student_id = %s;", (student_id,))
                    conn.commit()
                logger.error(f"Failed to create user account, student profile rolled back for {index_number}")
            return False, "Failed to create user account"
            
    except Exception as e:
        logger.error(f"Error creating student account for {index_number}: {e}")
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def reset_student_password(index_number, new_password=None):
    """Reset a student's password (admin function)"""
    conn = connect_to_db()
    if conn is None:
        logger.error("Error: Could not connect to database for password reset.")
        return False, None
    
    try:
        # Generate new password if not provided
        if new_password is None:
            new_password = index_number[-4:] + "2024"
        
        # Check if student exists
        with conn.cursor() as cur:
            cur.execute("SELECT user_id FROM users WHERE username = %s AND role = 'student';", (index_number,))
            user = cur.fetchone()
            
            if not user:
                return False, "Student account not found"
            
            # Update password
            cur.execute("""
                UPDATE users SET password = %s 
                WHERE username = %s AND role = 'student'
            """, (hash_password(new_password), index_number))
            conn.commit()
            
            logger.info(f"Password reset for student {index_number}")
            return True, new_password
            
    except Exception as e:
        logger.error(f"Error resetting password for {index_number}: {e}")
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def get_student_accounts():
    """Get all student accounts for admin management"""
    conn = connect_to_db()
    if conn is None:
        logger.error("Error: Could not connect to database.")
        return []
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT u.username, sp.full_name, u.created_at, sp.program, sp.year_of_study
                FROM users u
                LEFT JOIN student_profiles sp ON u.username = sp.index_number
                WHERE u.role = 'student'
                ORDER BY u.created_at DESC
            """)
            accounts = cur.fetchall()
            
            result = []
            for account in accounts:
                result.append({
                    'index_number': account[0],
                    'full_name': account[1] or 'N/A',
                    'created_at': account[2],
                    'program': account[3] or 'N/A',
                    'year_of_study': account[4] or 'N/A'
                })
            
            return result
            
    except Exception as e:
        logger.error(f"Error fetching student accounts: {e}")
        return []
    finally:
        conn.close()

def delete_student_account(index_number):
    """Delete a student account and profile (admin function)"""
    conn = connect_to_db()
    if conn is None:
        logger.error("Error: Could not connect to database for account deletion.")
        return False, "Database connection failed"
    
    try:
        with conn.cursor() as cur:
            # Check if student exists
            cur.execute("SELECT user_id FROM users WHERE username = %s AND role = 'student';", (index_number,))
            user = cur.fetchone()
            
            if not user:
                return False, "Student account not found"
            
            # Delete user account (this will cascade to sessions if any)
            cur.execute("DELETE FROM users WHERE username = %s AND role = 'student';", (index_number,))
            
            # Delete student profile (grades will be cascade deleted if foreign key is set up properly)
            cur.execute("DELETE FROM student_profiles WHERE index_number = %s;", (index_number,))
            
            conn.commit()
            logger.info(f"Student account and profile deleted for {index_number}")
            return True, "Account deleted successfully"
            
    except Exception as e:
        logger.error(f"Error deleting student account {index_number}: {e}")
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()