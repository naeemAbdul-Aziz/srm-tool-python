# menu.py
from pprint import pprint


from db import fetch_all_records, insert_student_record, connect_to_db
from utils import summarize_grades, calculate_grade
from logger import get_logger
from report_utils import export_summary_report_txt, export_summary_report_pdf
from auth import sign_up, login
from file_handler import read_student_records

logger = get_logger(__name__)

def show_admin_menu():
    print("\n===== ADMIN MENU =====")
    print("1. View all student records")
    print("2. View student by index number")
    print("3. Update student score")
    print("4. Export summary report to file")
    print("5. Bulk Import Student Records")  # New option
    print("6. Logout")

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
                        students = fetch_all_records()
                        found = False
                        for student in students:
                            if student["index_number"] == index:
                                print(f"Student {index} found:")
                                pprint(student)
                                found = True
                                break
                        if not found:
                            print(f"No student found with index number {index}.")
                    elif admin_choice == "3":
                        index = input("Enter index number to update: ")
                        try:
                            new_score = int(input("Enter new score (0-100): "))
                        except ValueError:
                            print("Invalid score. Must be a number.")
                            continue
                        students = fetch_all_records()
                        updated = False
                        for student in students:
                            if student["index_number"] == index:
                                student["score"] = new_score
                                student["grade"] = calculate_grade(new_score)
                                try:
                                    insert_student_record(connect_to_db(), student)
                                    print(f"Student {index} score updated to {new_score}.")
                                    updated = True
                                except Exception as e:
                                    logger.error(f"Failed to update student: {e}")
                                break
                        if not updated:
                            print(f"No student found with index number {index}.")
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
                        try:
                            insert_student_record(connect_to_db(), student)
                            print("Student added successfully.")
                        except Exception as e:
                            logger.error(f"Failed to add student: {e}")
                    elif admin_choice == "7":
                        students = fetch_all_records()
                        summary = summarize_grades(students)
                        print("Grade summary:")
                        pprint(summary)
                    elif admin_choice == "8":
                        print("Logging out...")
                        break
                    else:
                        print("Invalid option. Please choose between 1 and 8.")
            elif role == "student":
                while True:
                    show_student_menu()
                    student_choice = input("Choose an option: ")
                    if student_choice == "1":
                        students = fetch_all_records()
                        found = False
                        for student in students:
                            if student["index_number"] == username:
                                print(f"Your record:")
                                pprint(student)
                                found = True
                                break
                        if not found:
                            print("No record found for your index number.")
                    elif student_choice == "2":
                        students = fetch_all_records()
                        for student in students:
                            if student["index_number"] == username:
                                file_path = input("Enter filename to export your report as TXT (e.g. my_report.txt): ").strip()
                                if file_path:
                                    success = export_summary_report_txt([student], filename=file_path)
                                    if success:
                                        print(f"Your report exported to {file_path}.")
                                    else:
                                        print("Failed to export your report.")
                                else:
                                    print("Export cancelled.")
                                break
                    elif student_choice == "3":
                        students = fetch_all_records()
                        for student in students:
                            if student["index_number"] == username:
                                file_path = input("Enter filename to export your report as PDF (e.g. my_report.pdf): ").strip()
                                if file_path:
                                    success = export_summary_report_pdf([student], filename=file_path)
                                    if success:
                                        print(f"Your report exported to {file_path}.")
                                    else:
                                        print("Failed to export your report.")
                                else:
                                    print("Export cancelled.")
                                break
                    elif student_choice == "4":
                        print("Logging out...")
                        break
                    else:
                        print("Invalid option. Please choose between 1 and 4.")
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
        print("Error: Could not connect to database.")
        return

    successful_imports = 0
    for record in valid_records:
        try:
            record["grade"] = calculate_grade(record["score"])
            insert_student_record(conn, record)
            successful_imports += 1
        except Exception as e:
            print(f"Error importing record {record}: {e}")

    print("\nBulk Import Summary:")
    print(f"Total Records: {len(valid_records)}")
    print(f"Successfully Imported: {successful_imports}")
    print(f"Skipped: {len(valid_records) - successful_imports}")
