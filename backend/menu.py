# menu.py
from pprint import pprint

from db import fetch_all_records, insert_student_record, connect_to_db, fetch_student_by_index_number, update_student_score
from grade_util import summarize_grades, calculate_grade
from logger import get_logger
from report_utils import export_summary_report_pdf, export_summary_report_txt
from auth import sign_up, login
from file_handler import read_student_records

logger = get_logger(__name__)

def show_admin_menu():
    print("\n===== ADMIN MENU =====")
    print("1. View all student records")
    print("2. View student by index number")
    print("3. Update student score")
    print("4. Export summary report to TXT")
    print("5. Export summary report to PDF")
    print("6. Add a single student record")
    print("7. View grade summary")
    print("8. Bulk Import Student Records")
    print("9. Logout")

def show_student_menu():
    print("\n===== STUDENT MENU =====")
    print("1. View my record")
    print("2. Export my report to text file")
    print("3. Export my report to PDF")
    print("4. Logout")

def run_menu():
    while True:
        print("\nWelcome to Student Result Management Tool")
        print("1. Login")
        print("2. Sign Up")
        print("3. Exit")
        choice = input("Choose an option: ")
        if choice == "1":
            username, role = login()
            if not username:
                continue
            if role == "admin":
                while True:
                    show_admin_menu()
                    admin_choice = input("Choose an option: ")
                    if admin_choice == "1":
                        students = fetch_all_records()
                        if students:
                            print(f"Fetched {len(students)} student records.")
                            pprint(students)
                        else:
                            print("No student records found.")
                    elif admin_choice == "2":
                        index = input("Enter index number to search: ")
                        student = fetch_student_by_index_number(index)
                        if student:
                            print(f"Student {index} found:")
                            pprint(student)
                        else:
                            print(f"No student found with index number {index}.")
                    elif admin_choice == "3":
                        index = input("Enter index number to update: ")
                        try:
                            new_score = int(input("Enter new score (0-100): "))
                            if not (0 <= new_score <= 100):
                                print("Score must be between 0 and 100.")
                                continue
                        except ValueError:
                            print("Invalid score. Must be a number.")
                            continue

                        new_grade = calculate_grade(new_score)
                        success = update_student_score(index, new_score, new_grade)
                        if success:
                            print(f"Student {index} score updated to {new_score} (Grade: {new_grade}).")
                        else:
                            print(f"Failed to update score for student {index}. Check if index number exists.")
                    elif admin_choice == "4":
                        students = fetch_all_records()
                        if students:
                            file_path = input("Enter filename to export summary report as TXT (e.g. summary_report.txt): ").strip()
                            if file_path:
                                success = export_summary_report_txt(students, filename=file_path)
                                if success:
                                    print(f"Summary report exported to {file_path}.")
                                else:
                                    print("Failed to export summary report.")
                            else:
                                print("Export cancelled.")
                        else:
                            print("No student records found. Cannot export summary report.")
                    elif admin_choice == "5":
                        students = fetch_all_records()
                        if students:
                            file_path = input("Enter filename to export summary report as PDF (e.g. summary_report.pdf): ").strip()
                            if file_path:
                                success = export_summary_report_pdf(students, filename=file_path)
                                if success:
                                    print(f"Summary report exported to {file_path}.")
                                else:
                                    print("Failed to export PDF summary report.")
                            else:
                                print("Export cancelled.")
                        else:
                            print("No student records found. Cannot export PDF summary report.")
                    elif admin_choice == "6":
                        index = input("Enter index number: ")
                        name = input("Enter full name: ")
                        course = input("Enter course: ")
                        try:
                            score = int(input("Enter score (0-100): "))
                            if not (0 <= score <= 100):
                                print("Score must be between 0 and 100.")
                                continue
                        except ValueError:
                            print("Invalid score. Must be a number.")
                            continue
                        student = {
                            "index_number": index,
                            "full_name": name,
                            "course": course,
                            "score": score,
                            "grade": calculate_grade(score)
                        }
                        # Pass connection for single insert, but handle its closure outside if not within a 'with' block
                        conn_for_insert = connect_to_db()
                        if conn_for_insert:
                            success = insert_student_record(conn_for_insert, student)
                            conn_for_insert.close() # Close connection after use
                            if success:
                                print("Student added successfully.")
                            else:
                                print("Failed to add student. Index number might already exist or other database error.")
                        else:
                            print("Could not connect to database to add student.")
                    elif admin_choice == "7":
                        students = fetch_all_records()
                        if students:
                            summary = summarize_grades(students)
                            print("Grade summary:")
                            pprint(summary)
                        else:
                            print("No student records to summarize grades.")
                    elif admin_choice == "8":
                        bulk_import()
                    elif admin_choice == "9":
                        print("Logging out...")
                        break
                    else:
                        print("Invalid option. Please choose between 1 and 9.")
            elif role == "student":
                handle_student_menu(username)
        elif choice == "2":
            sign_up()
        elif choice == "3":
            print("Exiting...")
            break
        else:
            print("Invalid option. Please choose between 1 and 3.")

def bulk_import():
    file_path = input("Enter the path to the CSV/TXT file: ").strip()
    valid_records, errors = read_student_records(file_path)

    if errors:
        print("\nErrors encountered during file reading:")
        for error in errors:
            print(error)

    if not valid_records:
        print("\nNo valid records to import.")
        return

    conn = connect_to_db()
    if conn is None:
        print("Error: Could not connect to database for bulk import.")
        return

    successful_imports = 0
    try:
        for record in valid_records:
            record["grade"] = calculate_grade(record["score"])
            if insert_student_record(conn, record): # insert_student_record now returns True/False
                successful_imports += 1
            else:
                logger.warning(f"Skipped record {record['index_number']} due to an error during insertion.")
        conn.commit() # Commit once after all insertions in bulk import if inserts are not committing individually
        # NOTE: insert_student_record already commits individually on success, so this conn.commit() might be redundant
        # or it should be removed if we want individual transaction management, or insert_student_record should not commit.
        # For simplicity, keeping it as is, but for true bulk insert efficiency, a single commit at the end is better.
    except Exception as e:
        logger.error(f"Error during bulk import transaction: {e}")
        conn.rollback()
    finally:
        conn.close()

    print("\nBulk Import Summary:")
    print(f"Total Records: {len(valid_records)}")
    print(f"Successfully Imported: {successful_imports}")
    print(f"Skipped: {len(valid_records) - successful_imports}")

def handle_student_menu(username):
    while True:
        show_student_menu()
        student_choice = input("Choose an option: ").strip()

        if student_choice == "1":
            student = fetch_student_by_index_number(username)
            if student:
                print(f"Your record:")
                pprint(student)
            else:
                print("No record found for your index number.")

        elif student_choice == "2":
            student = fetch_student_by_index_number(username)
            if student:
                file_path = input("Enter filename to export your report as TXT (e.g. my_report.txt): ").strip()
                if file_path:
                    success = export_summary_report_txt([student], filename=file_path)
                    if success:
                        print(f"Your report exported to {file_path}.")
                    else:
                        print("Failed to export your report.")
                else:
                    print("Export cancelled.")
            else:
                print("No record found for your index number to export.")

        elif student_choice == "3":
            student = fetch_student_by_index_number(username)
            if student:
                file_path = input("Enter filename to export your report as PDF (e.g. my_report.pdf): ").strip()
                if file_path:
                    success = export_summary_report_pdf([student], filename=file_path)
                    if success:
                        print(f"Your report exported to {file_path}.")
                    else:
                        print("Failed to export your report.")
                else:
                    print("Export cancelled.")
            else:
                print("No record found for your index number to export.")

        elif student_choice == "4":
            print("Logging out...")
            break

        else:
            print("Invalid option. Please choose between 1 and 4.")