# menu.py - handles user interface and navigation for the student result management system

import getpass
from pprint import pprint
from db import (
    connect_to_db,
    fetch_all_records,
    insert_student_profile,
    insert_grade,
    fetch_student_by_index_number,
    update_student_score, # This function is still used for direct score updates
    insert_complete_student_record, # Used for bulk import
    fetch_course_by_code, # Added for resolving course_id
    fetch_semester_by_name, # Added for resolving semester_id
    insert_course, # Added for creating courses if not exist during grade add
    insert_semester # Added for creating semesters if not exist during grade add
)
from grade_util import summarize_grades, calculate_grade, calculate_gpa, get_grade_point
from logger import get_logger
from report_utils import export_summary_report_pdf, export_summary_report_txt
from auth import sign_up, create_user, create_student_account, reset_student_password, get_student_accounts, delete_student_account, authenticate_user
from bulk_importer import bulk_import_from_file
from file_handler import REQUIRED_FIELDS # Assuming this provides a list of required fields for bulk import
from course_management import (
    course_management_main,
    semester_management_main,
    initialize_enhanced_system
)
from session import session_manager

logger = get_logger(__name__)

def logout():
    """Handle user logout"""
    session_manager.clear_session()
    logger.info("User logged out successfully")
    print("You have been logged out successfully.")

def login(username, password):
    """Simple login function for compatibility"""
    return authenticate_user(username, password)


def show_admin_menu():
    """display the admin menu options"""
    print("\n===== ADMIN MENU =====")
    print("1. View all student records")
    print("2. View student by index number")
    print("3. Update student score")
    print("4. Export summary report to TXT")
    print("5. Export summary report to PDF")
    print("6. Add a single student record")
    print("7. View grade summary")
    print("8. Bulk Import Student Records")
    print("9. Course & Semester Management")
    print("10. Student Account Management")
    print("11. Logout")


def handle_admin_option(option):
    """Handle admin menu options."""
    try:
        if option == 1:
            logger.info("Admin selected: View all student records")
            conn = connect_to_db()
            if conn:
                records = fetch_all_records(conn)
                if records and records.get('students') and records.get('grades'):
                    print("\n--- All Student Records ---")
                    processed_records = process_records_for_display(records)
                    for student_idx, student_info in processed_records.items():
                        print(f"\nIndex Number: {student_idx}")
                        print(f"Name: {student_info['profile'].get('full_name', 'N/A')}")
                        print("Grades:")
                        if student_info['grades']:
                            for grade in student_info['grades']:
                                print(f"  - Course: {grade.get('course_code', 'N/A')} ({grade.get('course_title', 'N/A')}), Score: {grade.get('score', 'N/A')}, Grade: {grade.get('grade', 'N/A')}, Semester: {grade.get('semester_name', 'N/A')}")
                        else:
                            print("    No grades recorded for this student.")
                else:
                    print("No student records found.")
                conn.close()
            else:
                print("Could not connect to database.")

        elif option == 2:
            logger.info("Admin selected: View student by index number")
            index_num = input("Enter student index number: ").strip()
            conn = connect_to_db()
            if conn:
                student_data = fetch_student_by_index_number(conn, index_num)
                if student_data:
                    print(f"\n--- Student Profile for {index_num} ---")
                    print(f"Full Name: {student_data.get('full_name', 'N/A')}")
                    print(f"DOB: {student_data.get('dob', 'N/A')}")
                    print(f"Gender: {student_data.get('gender', 'N/A')}")
                    print(f"Email: {student_data.get('contact_email', 'N/A')}")
                    print(f"Phone: {student_data.get('contact_phone', 'N/A')}")
                    print(f"Program: {student_data.get('program', 'N/A')}")
                    print(f"Year of Study: {student_data.get('year_of_study', 'N/A')}")
                    
                    print("\n--- Grades ---")
                    if student_data.get('grades'):
                        for grade in student_data['grades']:
                            print(f"  - Course: {grade.get('course_code', 'N/A')} ({grade.get('course_title', 'N/A')}), Semester: {grade.get('semester_name', 'N/A')}, Academic Year: {grade.get('academic_year', 'N/A')}, Score: {grade.get('score', 'N/A')}, Grade: {grade.get('grade', 'N/A')}, Grade Point: {grade.get('grade_point', 'N/A')}")
                    else:
                        print("No grades found for this student.")
                else:
                    print("Student not found.")
                conn.close()
            else:
                print("Could not connect to database.")

        elif option == 3:
            logger.info("Admin selected: Update student score")
            index_num = input("Enter student index number to update score: ").strip()
            course_code = input("Enter course code: ").strip().upper()
            semester_name = input("Enter semester name (e.g., 'Alpha'): ").strip()
            academic_year = input("Enter academic year (e.g., '2023/2024'): ").strip()
            try:
                new_score = float(input("Enter new score: ").strip())
                if not (0 <= new_score <= 100):
                    print("Score must be between 0 and 100.")
                    return
                
                new_grade = calculate_grade(new_score)
                new_grade_point = get_grade_point(new_score)

                conn = connect_to_db()
                if conn:
                    # Resolve IDs first
                    student = fetch_student_by_index_number(conn, index_num)
                    course = fetch_course_by_code(conn, course_code)
                    semester = fetch_semester_by_name(conn, semester_name)

                    if not student:
                        print(f"Student with index number {index_num} not found.")
                        conn.close()
                        return
                    if not course:
                        print(f"Course with code {course_code} not found.")
                        conn.close()
                        return
                    if not semester:
                        print(f"Semester with name {semester_name} not found.")
                        conn.close()
                        return
                    
                    if update_student_score(conn, student['student_id'], course['course_id'], semester['semester_id'], new_score, new_grade, new_grade_point, academic_year):
                        print("Student score updated successfully.")
                    else:
                        print("Failed to update score. Check index number, course code, and semester combination.")
                    conn.close()
                else:
                    print("Could not connect to database.")
            except ValueError:
                print("Invalid score entered.")
            except Exception as e:
                logger.error(f"Error updating student score: {e}")
                print(f"An error occurred: {e}")


        elif option == 4:
            logger.info("Admin selected: Export summary report to TXT")
            conn = connect_to_db()
            if conn:
                records = fetch_all_records(conn)
                conn.close()
                if records and records.get('students'):
                    # The export functions expect a list of student records, potentially with nested grades
                    # process_records_for_display already structures this well
                    processed_records = process_records_for_display(records)
                    records_list_for_report = list(processed_records.values()) # Convert dict to list of student data
                    if export_summary_report_txt(records_list_for_report, "summary_report.txt"):
                        print("Summary report exported to summary_report.txt")
                    else:
                        print("Failed to export summary report.")
                else:
                    print("No records to export.")
            else:
                print("Could not connect to database.")

        elif option == 5:
            logger.info("Admin selected: Export summary report to PDF")
            conn = connect_to_db()
            if conn:
                records = fetch_all_records(conn)
                conn.close()
                if records and records.get('students'):
                    processed_records = process_records_for_display(records)
                    records_list_for_report = list(processed_records.values()) # Convert dict to list of student data
                    if export_summary_report_pdf(records_list_for_report, "summary_report.pdf"):
                        print("Summary report exported to summary_report.pdf")
                    else:
                        print("Failed to export summary report.")
                else:
                    print("No records to export.")
            else:
                print("Could not connect to database.")
                
        elif option == 6:
            logger.info("Admin selected: Add a single student record")
            print("\n--- ADD SINGLE STUDENT RECORD ---")
            index_number = input("Enter student index number (e.g., ug12345): ").strip()
            full_name = input("Enter student full name: ").strip()
            dob_str = input("Enter Date of Birth (YYYY-MM-DD, optional): ").strip()
            gender = input("Enter Gender (optional): ").strip()
            contact_email = input("Enter Contact Email (optional): ").strip()
            contact_phone = input("Enter Contact Phone (optional): ").strip() # Added phone
            program = input("Enter Program (optional): ").strip()
            year_of_study_str = input("Enter Year of Study (optional): ").strip()

            dob = None
            if dob_str:
                try:
                    from datetime import datetime
                    dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
                except ValueError:
                    print("Invalid DOB format. Skipping DOB. Please use YYYY-MM-DD.")
                    dob = None
            
            year_of_study = None
            if year_of_study_str:
                try:
                    year_of_study = int(year_of_study_str)
                except ValueError:
                    print("Invalid Year of Study. Skipping. Please enter a number.")
                    year_of_study = None

            conn = connect_to_db()
            if conn:
                student_id = insert_student_profile(conn, index_number, full_name, dob, gender, contact_email, contact_phone, program, year_of_study)
                if student_id:
                    print(f"Student '{full_name}' ({index_number}) added with ID: {student_id}.")
                    
                    # Optionally, ask to add a grade immediately
                    add_grade_now = input("Do you want to add a grade for this student now? (yes/no): ").strip().lower()
                    if add_grade_now == 'yes':
                        course_code = input("Enter course code: ").strip().upper()
                        course_title = input("Enter course title (will be created if new): ").strip()
                        credit_hours_str = input("Enter credit hours (will be created if new course): ").strip()
                        semester_name = input("Enter semester name (e.g., 'Alpha'): ").strip()
                        academic_year = input("Enter academic year (e.g., '2023/2024'): ").strip()
                        score_str = input("Enter score: ").strip()

                        try:
                            score = float(score_str)
                            credit_hours = int(credit_hours_str)
                            if not (0 <= score <= 100):
                                print("Score must be between 0 and 100. Grade not added.")
                                conn.close()
                                return

                            # Fetch course_id or insert if not exist
                            course = fetch_course_by_code(conn, course_code)
                            if not course:
                                course_id = insert_course(conn, course_code, course_title, credit_hours)
                                if not course_id:
                                    print("Failed to add course for grade. Please add course manually.")
                                    conn.close()
                                    return
                            else:
                                course_id = course['course_id']

                            # Fetch semester_id or insert if not exist
                            semester = fetch_semester_by_name(conn, semester_name)
                            if not semester:
                                # Placeholder dates if semester doesn't exist
                                current_year = datetime.now().year
                                start_date = datetime.strptime(f'09-01-{current_year}', '%m-%d-%Y').date()
                                end_date = datetime.strptime(f'12-31-{current_year}', '%m-%d-%Y').date()
                                if "spring" in semester_name.lower():
                                    start_date = datetime.strptime(f'01-01-{current_year}', '%m-%d-%Y').date()
                                    end_date = datetime.strptime(f'05-31-{current_year}', '%m-%d-%Y').date()

                                semester_id = insert_semester(conn, semester_name, start_date, end_date, academic_year)
                                if not semester_id:
                                    print("Failed to add semester for grade. Please add semester manually.")
                                    conn.close()
                                    return
                            else:
                                semester_id = semester['semester_id']
                                
                            grade = calculate_grade(score)
                            grade_point = get_grade_point(score)

                            if insert_grade(conn, student_id, course_id, semester_id, score, grade, grade_point, academic_year):
                                print("Grade added successfully for the student.")
                            else:
                                print("Failed to add grade.")
                        except ValueError:
                            print("Invalid numeric input for score or credit hours. Grade not added.")
                        except Exception as e:
                            logger.error(f"Error adding grade after student record: {e}")
                            print("An error occurred while adding the grade.")
                else:
                    print("Failed to add student record.")
                conn.close()
            else:
                print("Could not connect to database.")

        elif option == 7:
            logger.info("Admin selected: View grade summary")
            conn = connect_to_db()
            if conn:
                records = fetch_all_records(conn)
                conn.close()
                if records and records.get('grades'):
                    # Extract grades from the combined records
                    grades_only = [g.get('grade') for g in records['grades'] if g.get('grade') is not None]
                    if grades_only:
                        summary = summarize_grades(grades_only) # This expects a list of grades, not student objects
                        print("\n--- Grade Summary ---")
                        for grade, count in summary.items():
                            print(f"{grade}: {count}")
                    else:
                        print("No grades available for summary.")
                else:
                    print("No records found to summarize grades.")
            else:
                print("Could not connect to database.")

        elif option == 8:
            logger.info("Admin selected: Bulk Import Student Records")
            file_path = input("Enter the path to the bulk import file (e.g., students.csv): ").strip()
            semester_for_import = input("Enter the semester name for these records (e.g., 'Fall 2023'): ").strip()
            if not semester_for_import:
                print("Semester name is required for bulk import.")
                return

            handle_bulk_import(file_path, semester_for_import)
        
        elif option == 9:
            logger.info("Admin selected: Course & Semester Management")
            print("\n--- COURSE & SEMESTER MANAGEMENT ---")
            while True:
                print("\nSub-Menu:")
                print("1. Course Management")
                print("2. Semester Management")
                print("0. Back to Admin Menu")
                sub_choice = input("Choose an option: ").strip()

                if sub_choice == "1":
                    course_management_main()
                elif sub_choice == "2":
                    semester_management_main()
                elif sub_choice == "0":
                    break
                else:
                    print("Invalid option. Please try again.")
                input("\nPress Enter to continue...")

        elif option == 10:
            logger.info("Admin selected: Student Account Management")
            student_account_management_menu()
            
        elif option == 11:
            logger.info("Admin selected: Logout")
            logout()
            return
        else:
            logger.warning(f"Invalid admin menu option selected: {option}")
            print("Invalid option. Please try again.")
        
        input("\nPress Enter to continue...")
    
    except Exception as e:
        logger.error(f"Error handling admin menu option {option}: {e}")
        print("An error occurred while processing the admin menu option.")

def student_account_management_menu():
    """Student Account Management submenu for admins"""
    while True:
        print("\n===== STUDENT ACCOUNT MANAGEMENT =====")
        print("1. Create new student account")
        print("2. View all student accounts")
        print("3. Reset student password")
        print("4. Delete student account")
        print("5. Back to admin menu")
        
        choice = input("Enter your choice: ").strip()
        
        if choice == "1":
            create_new_student_account()
        elif choice == "2":
            view_all_student_accounts()
        elif choice == "3":
            reset_student_password_menu()
        elif choice == "4":
            delete_student_account_menu()
        elif choice == "5":
            break
        else:
            print("Invalid option. Please try again.")
        
        input("\nPress Enter to continue...")

def create_new_student_account():
    """Create a new student account"""
    print("\n--- Create New Student Account ---")
    
    index_number = input("Enter student index number (e.g., UG20226324): ").strip()
    if not index_number:
        print("Index number cannot be empty.")
        return
    
    full_name = input("Enter student full name: ").strip()
    if not full_name:
        print("Full name cannot be empty.")
        return
    
    use_default = input("Use default password (last 4 digits + 2024)? (y/n): ").strip().lower()
    password = None
    if use_default != 'y':
        password = input("Enter custom password: ").strip()
        if not password:
            print("Password cannot be empty.")
            return
    
    success, result = create_student_account(index_number, full_name, password)
    
    if success and isinstance(result, dict):
        print(f"\n✓ Student account created successfully!")
        print(f"Index Number: {result.get('index_number', 'N/A')}")
        print(f"Full Name: {result.get('full_name', 'N/A')}")
        print(f"Password: {result.get('password', 'N/A')}")
        print(f"Student ID: {result.get('student_id', 'N/A')}")
        print("\nProvide these credentials to the student for login.")
    else:
        error_msg = result if result else "Unknown error occurred"
        print(f"\n✗ Failed to create student account: {error_msg}")

def view_all_student_accounts():
    """View all student accounts"""
    print("\n--- All Student Accounts ---")
    
    accounts = get_student_accounts()
    if not accounts:
        print("No student accounts found.")
        return
    
    print(f"\nFound {len(accounts)} student accounts:")
    print("-" * 80)
    print(f"{'Index Number':<15} {'Full Name':<25} {'Program':<15} {'Year':<6} {'Created'}")
    print("-" * 80)
    
    for account in accounts:
        created_date = account.get('created_at')
        created_str = created_date.strftime('%Y-%m-%d') if created_date else 'N/A'
        index_num = account.get('index_number', 'N/A')
        full_name = account.get('full_name', 'N/A')
        program = account.get('program', 'N/A')
        year = account.get('year_of_study', 'N/A')
        print(f"{index_num:<15} {full_name:<25} {program:<15} {year:<6} {created_str}")

def reset_student_password_menu():
    """Reset a student's password"""
    print("\n--- Reset Student Password ---")
    
    index_number = input("Enter student index number: ").strip()
    if not index_number:
        print("Index number cannot be empty.")
        return
    
    use_default = input("Use default password (last 4 digits + 2024)? (y/n): ").strip().lower()
    new_password = None
    if use_default != 'y':
        new_password = input("Enter new password: ").strip()
        if not new_password:
            print("Password cannot be empty.")
            return
    
    success, result = reset_student_password(index_number, new_password)
    
    if success:
        print(f"\n✓ Password reset successfully!")
        print(f"Index Number: {index_number}")
        print(f"New Password: {result}")
        print("\nProvide the new password to the student.")
    else:
        print(f"\n✗ Failed to reset password: {result}")

def delete_student_account_menu():
    """Delete a student account"""
    print("\n--- Delete Student Account ---")
    
    index_number = input("Enter student index number: ").strip()
    if not index_number:
        print("Index number cannot be empty.")
        return
    
    confirm = input(f"Are you sure you want to delete account for {index_number}? (yes/no): ").strip().lower()
    if confirm != 'yes':
        print("Account deletion cancelled.")
        return
    
    success, result = delete_student_account(index_number)
    
    if success:
        print(f"\n✓ Student account deleted successfully!")
        print(f"Index Number: {index_number}")
    else:
        print(f"\n✗ Failed to delete account: {result}")

def show_student_menu():
    """Display the student menu options."""
    print("\n===== STUDENT MENU =====")
    print("1. View my grades")
    print("2. View my profile")
    print("3. Generate personal academic report (PDF)")
    print("4. Logout")

def student_menu_loop(user_data):
    """student menu loop"""
    logger.info(f"student {user_data.get('username', 'N/A')} entered student menu.")
    while True:
        show_student_menu()
        choice = input("Enter your choice: ").strip()
        index_number = user_data['username'] # For student, username is index_number

        if choice == "1":
            logger.info("Student selected: View my grades")
            conn = connect_to_db()
            if conn:
                student_data = fetch_student_by_index_number(conn, index_number)
                conn.close()
                if student_data and student_data.get('grades'):
                    print(f"Grades for {student_data['full_name']} ({index_number}):")
                    for grade in student_data['grades']:
                        print(f"  - Course: {grade.get('course_code', 'N/A')} ({grade.get('course_title', 'N/A')}), Score: {grade.get('score', 'N/A')}, Grade: {grade.get('grade', 'N/A')}, Semester: {grade.get('semester_name', 'N/A')}")
                else:
                    print("No grades found.")
            else:
                print("Could not connect to database.")

        elif choice == "2":
            logger.info("Student selected: View my profile")
            conn = connect_to_db()
            if conn:
                student_data = fetch_student_by_index_number(conn, index_number)
                conn.close()
                if student_data:
                    print(f"Profile for {student_data['full_name']} ({index_number}):")
                    print(f"  - Program: {student_data.get('program', 'N/A')}")
                    print(f"  - Year of Study: {student_data.get('year_of_study', 'N/A')}")
                else:
                    print("Profile not found.")
            else:
                print("Could not connect to database.")

        elif choice == "3":
            logger.info("Student selected: Generate personal academic report (PDF)")
            try:
                conn = connect_to_db()
                if conn:
                    student_data = fetch_student_by_index_number(conn, index_number)
                    conn.close()
                    if student_data:
                        # The export function expects a list of student records, so wrap it
                        if export_summary_report_pdf([{'profile': student_data, 'grades': student_data.get('grades', [])}], f"{index_number}_transcript.pdf"):
                            print(f"Personal academic report exported to {index_number}_transcript.pdf")
                        else:
                            print("Failed to generate personal academic report.")
                    else:
                        print("Student profile not found to generate report.")
                else:
                    print("Could not connect to database.")
            except Exception as e:
                logger.error(f"Error generating academic report: {e}")
                print("An error occurred while generating the report.")

        elif choice == "4":
            logger.info("Student selected: Logout")
            logout()
            break

        else:
            logger.warning(f"Invalid student menu option selected: {choice}")
            print("Invalid option. Please try again.")

        input("\nPress Enter to continue...")

def process_records_for_display(records):
    """
    Process and organize records for better display in the CLI.
    Groups grades under each student.
    """
    logger.debug(f"Processing records: {records}")
    processed_records = {}
    
    # First, populate student profiles
    for student in records.get('students', []):
        processed_records[student['index_number']] = {
            'profile': student,
            'grades': []
        }
    
    # Then, add grades to their respective students
    for grade in records.get('grades', []):
        student_idx = grade.get('index_number') # Use 'index_number' from the joined grade record
        if student_idx and student_idx in processed_records:
            processed_records[student_idx]['grades'].append(grade)
    
    return processed_records

def handle_bulk_import(file_path, semester_for_import):
    """Handle bulk import of student records."""
    try:
        conn = connect_to_db()
        if not conn:
            print("Could not connect to database for bulk import.")
            return

        # Read the file content
        with open(file_path, 'r') as f:
            csv_data = f.read()

        # Simple CSV parsing (you might want a more robust CSV parser for production)
        lines = csv_data.strip().split('\n')
        if not lines:
            print("CSV file is empty.")
            conn.close()
            return

        headers = [h.strip() for h in lines[0].split(',')]
        records_to_import = []
        for line in lines[1:]:
            if line.strip():
                values = [v.strip() for v in line.split(',')]
                record = dict(zip(headers, values))
                records_to_import.append(record)

        results = bulk_import_from_file(file_path, records_to_import, semester_for_import)
        conn.close()
        logger.info("Bulk import completed.")
        print(f"\nBulk Import Results:")
        print(f"Message: {results.get('message', 'N/A')}")
        print(f"Total records processed: {results.get('total_records', 0)}")
        print(f"Successfully imported: {results.get('successful_imports', 0)}")
        print(f"Failed imports: {results.get('failed_imports', 0)}")
        if results.get('errors'):
            print("\nErrors during import:")
            for error in results['errors']:
                print(f"- {error}")
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
    except Exception as e:
        logger.error(f"Error during bulk import: {e}")
        print(f"An error occurred during bulk import: {e}")

def admin_menu_loop(user_data):
    """Admin menu loop."""
    logger.info(f"Admin {user_data.get('username', 'N/A')} entered admin menu.")
    while True:
        show_admin_menu()
        try:
            option = int(input("Select an option: ").strip())
            handle_admin_option(option)
            if option == 11:  # Logout option
                break
        except ValueError:
            logger.warning("Invalid input for admin menu option. Must be an integer.")
            print("Please enter a valid option.")
        except Exception as e:
            logger.error(f"Error in admin menu loop: {e}")
            print("An error occurred. Please try again.")

def main_menu_loop():
    """main application loop for login and sign up"""
    initialize_enhanced_system() # Ensure tables are created on startup
    while True:
        print("\nWelcome to Student Result Management System!")
        print("1. Login")
        print("2. Sign Up (New Admin)")
        print("3. Exit")
        
        try:
            choice = input("Enter your choice: ").strip()

            if choice == "1":
                username = input("Enter username (Index Number for Students): ").strip()
                password = getpass.getpass("Enter password: ").strip()
                user_data = login(username, password)
                
                if user_data:
                    if user_data.get('role') == 'admin':
                        admin_menu_loop(user_data)
                    elif user_data.get('role') == 'student':
                        student_menu_loop(user_data)
                    else:
                        print("Unknown user role. Please contact administrator.")
                # login function already prints error messages
                        
            elif choice == "2":
                # Only allow admin signup from here for security/control
                try:
                    if sign_up(role='admin'):
                        print("admin sign up process completed. you can now log in.")
                        logger.info("new admin user signed up successfully")
                    else:
                        print("sign up failed. username might already exist or an error occurred.")
                except Exception as e:
                    print("error during sign up. please try again.")
                    logger.error(f"sign up error: {e}")
                
            elif choice == "3":
                print("exiting...")
                logger.info("user exiting application")
                break
                
            else:
                print("invalid option. please choose between 1 and 3.")
                logger.warning(f"invalid main menu choice: {choice}")
                
        except KeyboardInterrupt:
            print("\n\nexiting application...")
            logger.info("application interrupted by user")
            break
        except Exception as e:
            print("an unexpected error occurred. please try again.")
            logger.error(f"unexpected error in main menu: {e}")

if __name__ == "__main__":
    main_menu_loop()

