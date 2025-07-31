#!/usr/bin/env python3
"""
Course Management Module
========================

This module provides CLI functions for managing courses and semesters.
It's designed to be imported and used by the main menu system.

Functions:
- Course Management: Add, edit, delete, and list courses
- Semester Management: Set up academic calendar, manage current semester
- Enhanced Grade Management: Course-specific grading with proper validation
"""

from db import (
    connect_to_db,
    create_tables_if_not_exist, # Updated function name
    insert_course,
    fetch_all_courses,
    fetch_course_by_code,
    update_course,
    delete_course,
    insert_semester,
    fetch_all_semesters,
    fetch_current_semester,
    set_current_semester,
    update_semester, # Added for completeness as it exists in db.py
    delete_semester # Added for completeness as it exists in db.py
)
from logger import get_logger
from datetime import datetime
from psycopg2.pool import SimpleConnectionPool
from config import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT

logger = get_logger(__name__)

# Initialize connection pool
connection_pool = None

def initialize_connection_pool(minconn, maxconn):
    """Initialize the database connection pool."""
    global connection_pool
    try:
        connection_pool = SimpleConnectionPool(
            minconn,
            maxconn,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        if connection_pool:
            logger.info("Connection pool initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing connection pool: {e}")

# Update connect_to_db to use the connection pool
def connect_to_db():
    """Get a connection from the pool."""
    try:
        if connection_pool:
            return connection_pool.getconn()
        else:
            logger.error("Connection pool is not initialized.")
            return None
    except Exception as e:
        logger.error(f"Error getting connection from pool: {e}")
        return None

def release_connection(conn):
    """Release a connection back to the pool."""
    try:
        if connection_pool and conn:
            connection_pool.putconn(conn)
    except Exception as e:
        logger.error(f"Error releasing connection back to pool: {e}")

def display_courses_menu():
    """Display the course management menu"""
    print("\n=== COURSE MANAGEMENT ===")
    print("1. List all courses")
    print("2. Add new course")
    print("3. Edit course")
    print("4. Delete course")
    print("5. Search course")
    print("0. Back to main menu")
    return input("Choose an option: ").strip()

def display_semesters_menu():
    """Display the semester management menu"""
    print("\n=== SEMESTER MANAGEMENT ===")
    print("1. List all semesters")
    print("2. Add new semester")
    print("3. Set current semester")
    print("4. View current semester")
    print("0. Back to main menu")
    return input("Choose an option: ").strip()

def list_all_courses():
    """List all courses in the system."""
    print("\n--- ALL COURSES ---")
    conn = connect_to_db()
    if conn:
        try:
            courses = fetch_all_courses(conn)
            if courses:
                for course in courses:
                    print(f"Code: {course['course_code']}, Title: {course['course_title']}, Credits: {course['credit_hours']}")
            else:
                print("No courses found.")
        except Exception as e:
            logger.error(f"Error listing courses: {e}")
            print("Error retrieving courses.")
        finally:
            conn.close()

def validate_course_code(course_code):
    """Validate course code format."""
    if not course_code or not course_code.isalnum() or len(course_code) > 10:
        return False, "Course code must be alphanumeric and up to 10 characters."
    return True, None

def is_duplicate_course(conn, course_code):
    """Check if a course code already exists."""
    try:
        existing_courses = fetch_all_courses(conn)
        return any(course['course_code'].lower() == course_code.lower() for course in existing_courses)
    except Exception as e:
        logger.error(f"Error checking duplicate course: {e}")
        return False

def add_new_course():
    """Add a new course to the system."""
    print("\n--- ADD NEW COURSE ---")
    course_code = input("Enter course code (e.g., MATH101): ").strip().upper()
    is_valid, error = validate_course_code(course_code)
    if not is_valid:
        print(error)
        return

    course_title = input("Enter course title (e.g., Calculus I): ").strip()
    try:
        credit_hours = int(input("Enter credit hours (e.g., 3): ").strip())
        if credit_hours <= 0:
            print("Credit hours must be a positive number.")
            return
    except ValueError:
        print("Invalid credit hours. Please enter a number.")
        return

    conn = connect_to_db()
    if conn:
        try:
            if is_duplicate_course(conn, course_code):
                print(f"Course code '{course_code}' already exists. Please use a different code.")
                return

            if insert_course(conn, course_code, course_title, credit_hours):
                print(f"Course '{course_title}' ({course_code}) added successfully.")
            else:
                print("Failed to add course. It might already exist or an error occurred.")
        except Exception as e:
            logger.error(f"Error adding new course: {e}")
            print("Error adding new course.")
        finally:
            conn.close()

def edit_course():
    """Edit an existing course."""
    print("\n--- EDIT COURSE ---")
    course_code = input("Enter the CODE of the course to edit: ").strip().upper()
    conn = connect_to_db()
    if conn:
        try:
            course = fetch_course_by_code(conn, course_code)
            if course:
                print(f"Current Course: {course['course_title']} ({course['course_code']}), Credits: {course['credit_hours']}")
                new_title = input(f"Enter new title (leave blank to keep '{course['course_title']}'): ").strip()
                new_credits_str = input(f"Enter new credit hours (leave blank to keep {course['credit_hours']}): ").strip()

                updates = {}
                if new_title:
                    updates['course_title'] = new_title
                if new_credits_str:
                    try:
                        new_credits = int(new_credits_str)
                        if new_credits > 0:
                            updates['credit_hours'] = new_credits
                        else:
                            print("New credit hours must be a positive number. Not updating credits.")
                    except ValueError:
                        print("Invalid credit hours. Not updating credits.")

                if updates:
                    if update_course(conn, course['course_id'], updates):
                        print(f"Course '{course_code}' updated successfully.")
                    else:
                        print(f"Failed to update course '{course_code}'.")
                else:
                    print("No changes specified.")
            else:
                print(f"Course with code '{course_code}' not found.")
        except Exception as e:
            logger.error(f"Error editing course {course_code}: {e}")
            print("Error editing course.")
        finally:
            conn.close()

def delete_course_cli():
    """Delete a course from the system."""
    print("\n--- DELETE COURSE ---")
    course_code = input("Enter the CODE of the course to delete: ").strip().upper()
    conn = connect_to_db()
    if conn:
        try:
            course = fetch_course_by_code(conn, course_code)
            if course:
                confirm = input(f"Are you sure you want to delete '{course['course_title']}' ({course_code})? (yes/no): ").strip().lower()
                if confirm == 'yes':
                    if delete_course(conn, course['course_id']):
                        print(f"Course '{course_code}' deleted successfully.")
                    else:
                        print(f"Failed to delete course '{course_code}'.")
                else:
                    print("Course deletion cancelled.")
            else:
                print(f"Course with code '{course_code}' not found.")
        except Exception as e:
            logger.error(f"Error deleting course {course_code}: {e}")
            print("Error deleting course.")
        finally:
            conn.close()

def search_course():
    """Search for a course by code or title."""
    print("\n--- SEARCH COURSE ---")
    query = input("Enter course code or title to search: ").strip()
    conn = connect_to_db()
    if conn:
        try:
            courses = fetch_all_courses(conn) # Fetch all and filter in app for simplicity
            found_courses = [c for c in courses if query.lower() in c['course_code'].lower() or query.lower() in c['course_title'].lower()]
            
            if found_courses:
                print("\nFound Courses:")
                for course in found_courses:
                    print(f"Code: {course['course_code']}, Title: {course['course_title']}, Credits: {course['credit_hours']}")
            else:
                print(f"No courses found matching '{query}'.")
        except Exception as e:
            logger.error(f"Error searching courses: {e}")
            print("Error searching courses.")
        finally:
            conn.close()

def list_all_semesters():
    """List all semesters in the system."""
    print("\n--- ALL SEMESTERS ---")
    conn = connect_to_db()
    if conn:
        try:
            semesters = fetch_all_semesters(conn)
            if semesters:
                for s in semesters:
                    current_status = "(Current)" if s['is_current'] else ""
                    print(f"ID: {s['semester_id']}, Name: {s['semester_name']}, Start: {s['start_date'].strftime('%Y-%m-%d')}, End: {s['end_date'].strftime('%Y-%m-%d')} {current_status}")
            else:
                print("No semesters found.")
        except Exception as e:
            logger.error(f"Error listing semesters: {e}")
            print("Error retrieving semesters.")
        finally:
            conn.close()

def validate_semester_dates(start_date, end_date):
    """Validate semester start and end dates."""
    if start_date >= end_date:
        return False, "Start date must be before end date."
    return True, None

def add_new_semester():
    """Add a new semester to the system."""
    print("\n--- ADD NEW SEMESTER ---")
    semester_name = input("Enter semester name (e.g., Fall 2023): ").strip()
    start_date_str = input("Enter start date (YYYY-MM-DD): ").strip()
    end_date_str = input("Enter end date (YYYY-MM-DD): ").strip()

    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        is_valid, error = validate_semester_dates(start_date, end_date)
        if not is_valid:
            print(error)
            return
    except ValueError:
        print("Invalid date format. Please use YYYY-MM-DD.")
        return

    conn = connect_to_db()
    if conn:
        try:
            # Check if semester name already exists to prevent duplicates
            existing_semesters = fetch_all_semesters(conn)
            if any(s['semester_name'].lower() == semester_name.lower() for s in existing_semesters):
                print(f"Semester '{semester_name}' already exists.")
                return

            if insert_semester(conn, semester_name, start_date, end_date):
                print(f"Semester '{semester_name}' added successfully.")
            else:
                print("Failed to add semester. An error occurred.")
        except Exception as e:
            logger.error(f"Error adding new semester: {e}")
            print("Error adding new semester.")
        finally:
            conn.close()

def set_current_semester(conn, semester_id):
    """Set a semester as the current active semester."""
    try:
        with conn.cursor() as cur:
            # Reset all semesters to not current
            cur.execute("UPDATE semesters SET is_current = FALSE;")
            # Set the selected semester as current
            cur.execute("UPDATE semesters SET is_current = TRUE WHERE semester_id = %s;", (semester_id,))
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Error setting current semester: {e}")
        conn.rollback()
        return False

def set_current_semester_cli():
    """Set an existing semester as the current active semester."""
    print("\n--- SET CURRENT SEMESTER ---")
    semester_id_str = input("Enter the ID of the semester to set as current: ").strip()
    try:
        semester_id = int(semester_id_str)
    except ValueError:
        print("Invalid semester ID. Please enter a number.")
        return

    conn = connect_to_db()
    if conn:
        try:
            if set_current_semester(conn, semester_id):
                print(f"Semester ID {semester_id} set as current successfully.")
            else:
                print(f"Failed to set semester ID {semester_id} as current. It might not exist.")
        except Exception as e:
            logger.error(f"Error setting current semester: {e}")
            print("Error setting current semester.")
        finally:
            conn.close()

def view_current_semester():
    """View the currently set active semester."""
    print("\n--- CURRENT SEMESTER ---")
    conn = connect_to_db()
    if conn:
        try:
            current = fetch_current_semester(conn)
            logger.info("Viewing the current semester.")
            if current:
                print(f"Current Semester: {current['semester_name']} (ID: {current['semester_id']})")
                print(f"  Start Date: {current['start_date'].strftime('%Y-%m-%d')}")
                print(f"  End Date: {current['end_date'].strftime('%Y-%m-%d')}")
            else:
                print("No current semester set or found.")
        except Exception as e:
            logger.error(f"Error viewing current semester: {e}")
            print("Error retrieving current semester.")
        finally:
            conn.close()

def initialize_enhanced_system():
    """
    Initializes the enhanced system by ensuring tables exist and initializing the connection pool.
    This should be called once at application start-up.
    """
    logger.info("Initializing enhanced system.")
    try:
        initialize_connection_pool(minconn=1, maxconn=10)
        conn = connect_to_db()
        if conn:
            create_tables_if_not_exist(conn)
            logger.info("Database tables checked/created successfully.")
            release_connection(conn)
        else:
            logger.error("Failed to connect to database for initialization.")
            print("Failed to connect to database for initialization.")
    except Exception as e:
        logger.error(f"Error initializing enhanced system: {e}")
        print("Error initializing enhanced system.")

def validate_menu_choice(choice, valid_choices):
    """Validate menu choice against a list of valid options."""
    if choice not in valid_choices:
        print("Invalid option. Please try again.")
        return False
    return True

def course_management_main():
    """Main course management function"""
    while True:
        choice = display_courses_menu()
        if not validate_menu_choice(choice, ["1", "2", "3", "4", "5", "0"]):
            continue

        if choice == "1":
            list_all_courses()
        elif choice == "2":
            add_new_course()
        elif choice == "3":
            edit_course()
        elif choice == "4":
            delete_course_cli()
        elif choice == "5":
            search_course()
        elif choice == "0":
            break

        input("\nPress Enter to continue...")

def semester_management_main():
    """Main semester management function"""
    while True:
        choice = display_semesters_menu()
        if not validate_menu_choice(choice, ["1", "2", "3", "4", "0"]):
            continue

        if choice == "1":
            list_all_semesters()
        elif choice == "2":
            add_new_semester()
        elif choice == "3":
            set_current_semester_cli()
        elif choice == "4":
            view_current_semester()
        elif choice == "0":
            break

        input("\nPress Enter to continue...")

if __name__ == "__main__":
    # Example usage if this module is run directly
    # This block won't typically run if imported by menu.py
    print("Running Course and Semester Management Module directly...")
    initialize_enhanced_system()
    # You could uncomment one of these to test independently:
    # course_management_main()
    # semester_management_main()