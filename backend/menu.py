# menu.py - handles user interface and navigation for the student result management system

from pprint import pprint
from db import (
    connect_to_db,
    fetch_all_records,
    insert_student_profile,
    insert_grade,
    fetch_student_by_index_number,
    update_student_score
)
from grade_util import summarize_grades, calculate_grade
from logger import get_logger
from report_utils import export_summary_report_pdf, export_summary_report_txt
from auth import sign_up, login
from bulk_importer import bulk_import_from_file
from file_handler import REQUIRED_FIELDS
from course_management import (
    course_management_main,
    semester_management_main,
    initialize_enhanced_system
)

logger = get_logger(__name__)


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
    print("10. Logout")


def show_student_menu(index_number):
    """display and handle student menu interactions"""
    logger.info(f"showing student menu for index: {index_number}")
    print("\n===== STUDENT MENU =====")
    print("1. View your profile and grades")
    print("2. Logout")

    try:
        choice = input("Choose an option: ").strip()
        if choice == "1":
            logger.info(f"student {index_number} viewing their profile and grades")
            conn = connect_to_db()
            if conn:
                try:
                    student_data = fetch_student_by_index_number(conn, index_number)
                    if student_data:
                        print("\n📘 Your Profile:")
                        pprint(student_data["profile"])
                        print("\n📊 Your Grades:")
                        pprint(student_data["grades"])
                        print("\n📈 Grade Summary:")
                        summary = summarize_grades(student_data["grades"])
                        pprint(summary)
                        logger.info(f"successfully displayed profile for student {index_number}")
                    else:
                        print("could not fetch your records.")
                        logger.warning(f"no records found for student {index_number}")
                except Exception as e:
                    print("error retrieving your data. please try again.")
                    logger.error(f"error fetching student data for {index_number}: {e}")
                finally:
                    conn.close()
            else:
                print("database connection failed. please try again later.")
                logger.error("database connection failed in student menu")
        elif choice == "2":
            logger.info(f"student {index_number} logging out")
            return
        else:
            print("invalid choice.")
            logger.warning(f"invalid menu choice '{choice}' from student {index_number}")
    except Exception as e:
        print("an error occurred. please try again.")
        logger.error(f"error in student menu for {index_number}: {e}")


def admin_menu_loop():
    """handle the admin menu interactions"""
    logger.info("entering admin menu loop")
    
    while True:
        try:
            show_admin_menu()
            admin_choice = input("Choose an option: ").strip()
            logger.debug(f"admin selected option: {admin_choice}")

            if admin_choice == "1":
                # view all student records
                try:
                    logger.info("admin viewing all student records")
                    records = fetch_all_records()
                    if records:
                        pprint(records)
                        logger.info(f"displayed {len(records)} student records")
                    else:
                        print("no records found or database connection failed.")
                        logger.warning("no records found when admin tried to view all")
                except Exception as e:
                    print("error retrieving records. please try again.")
                    logger.error(f"error fetching all records: {e}")

            elif admin_choice == "2":
                # view student by index number
                try:
                    index_number = input("Enter student index number: ").strip()
                    logger.info(f"admin searching for student: {index_number}")
                    
                    conn = connect_to_db()
                    if conn:
                        try:
                            student_data = fetch_student_by_index_number(conn, index_number)
                            if student_data:
                                pprint(student_data)
                                logger.info(f"displayed data for student: {index_number}")
                            else:
                                print("no data found for that index number.")
                                logger.warning(f"no data found for student: {index_number}")
                        finally:
                            conn.close()
                    else:
                        print("database connection failed.")
                        logger.error("database connection failed when viewing student")
                except Exception as e:
                    print("error retrieving student data. please try again.")
                    logger.error(f"error fetching student {index_number}: {e}")

            elif admin_choice == "3":
                # update student score
                try:
                    index_number = input("Enter student index number: ").strip()
                    logger.info(f"admin updating score for student: {index_number}")
                    
                    # first, fetch and display current grades for the student
                    conn = connect_to_db()
                    if conn:
                        try:
                            student_data = fetch_student_by_index_number(conn, index_number)
                            
                            if student_data and student_data["grades"]:
                                print(f"\n📚 Current grades for {student_data['profile']['name']}:")
                                for i, grade in enumerate(student_data["grades"], 1):
                                    print(f"{i}. {grade['course_code']} - {grade['course_title']}: {grade['score']} ({grade['letter_grade']})")
                                
                                try:
                                    choice_idx = int(input("\nSelect course number to update: ")) - 1
                                    if 0 <= choice_idx < len(student_data["grades"]):
                                        selected_grade = student_data["grades"][choice_idx]
                                        course_code = selected_grade["course_code"]
                                        
                                        print(f"\nUpdating score for {course_code} - {selected_grade['course_title']}")
                                        print(f"Current score: {selected_grade['score']}")
                                        
                                        try:
                                            new_score = float(input("Enter new score (0-100): "))
                                            if not (0 <= new_score <= 100):
                                                print("score must be between 0 and 100")
                                                continue
                                                
                                            new_grade = calculate_grade(new_score)
                                            
                                            if update_student_score(index_number, course_code, new_score, new_grade):
                                                print(f"✅ score updated successfully! new grade: {new_grade}")
                                                logger.info(f"score updated for {index_number}, course {course_code}: {new_score}")
                                            else:
                                                print("❌ failed to update score.")
                                                logger.error(f"failed to update score for {index_number}, course {course_code}")
                                        except ValueError:
                                            print("invalid score. must be a number.")
                                            logger.warning("invalid score input during update")
                                    else:
                                        print("invalid selection.")
                                        logger.warning(f"invalid course selection during score update")
                                except ValueError:
                                    print("invalid input. please enter a number.")
                                    logger.warning("invalid course number input during score update")
                            else:
                                print("no grades found for this student or student doesn't exist.")
                                logger.warning(f"no grades found for student {index_number} during score update")
                        finally:
                            conn.close()
                    else:
                        print("database connection failed.")
                        logger.error("database connection failed during score update")
                except Exception as e:
                    print("error updating student score. please try again.")
                    logger.error(f"error during score update: {e}")

            elif admin_choice == "4":
                # export summary report to txt
                try:
                    logger.info("admin exporting summary report to txt")
                    records = fetch_all_records()
                    if records:
                        if export_summary_report_txt(records):
                            print("📄 summary report exported to summary_report.txt")
                            logger.info("successfully exported txt report")
                        else:
                            print("failed to export txt report")
                            logger.error("failed to export txt report")
                    else:
                        print("no records found to export.")
                        logger.warning("no records available for txt export")
                except Exception as e:
                    print("error exporting txt report. please try again.")
                    logger.error(f"error exporting txt report: {e}")

            elif admin_choice == "5":
                # export summary report to pdf
                try:
                    logger.info("admin exporting summary report to pdf")
                    records = fetch_all_records()
                    if records:
                        if export_summary_report_pdf(records):
                            print("📄 summary report exported to summary_report.pdf")
                            logger.info("successfully exported pdf report")
                        else:
                            print("failed to export pdf report")
                            logger.error("failed to export pdf report")
                    else:
                        print("no records found to export.")
                        logger.warning("no records available for pdf export")
                except Exception as e:
                    print("error exporting pdf report. please try again.")
                    logger.error(f"error exporting pdf report: {e}")

            elif admin_choice == "6":
                # add a single student record
                try:
                    logger.info("admin adding single student record")
                    profile = {}
                    grade = {}
                    
                    # collect student profile information
                    profile["index_number"] = input("Index Number: ").strip()
                    profile["name"] = input("Full Name: ").strip()
                    profile["program"] = input("Program: ").strip()
                    profile["year_of_study"] = input("Year of Study: ").strip()
                    profile["contact_info"] = input("Contact Info: ").strip()

                    # collect grade information
                    grade["index_number"] = profile["index_number"]
                    grade["course_code"] = input("Course Code: ").strip()
                    grade["course_title"] = input("Course Title: ").strip()
                    
                    try:
                        grade["score"] = float(input("Score (0-100): "))
                        if not (0 <= grade["score"] <= 100):
                            print("score must be between 0 and 100")
                            continue
                    except ValueError:
                        print("invalid score. must be a number.")
                        continue

                    try:
                        grade["credit_hours"] = int(input("Credit Hours: "))
                    except ValueError:
                        print("credit hours must be an integer.")
                        continue

                    grade["semester"] = input("Semester: ").strip()
                    grade["academic_year"] = input("Academic Year: ").strip()
                    grade["letter_grade"] = calculate_grade(grade["score"])

                    # insert the record
                    conn = connect_to_db()
                    if conn:
                        try:
                            if insert_student_profile(conn, profile) and insert_grade(conn, grade):
                                print("student record inserted successfully.")
                                logger.info(f"successfully added student record for {profile['index_number']}")
                            else:
                                print("failed to insert student record.")
                                logger.error(f"failed to insert student record for {profile['index_number']}")
                        except Exception as e:
                            print(f"error inserting record: {e}")
                            logger.error(f"error inserting student record: {e}")
                            conn.rollback()
                        finally:
                            conn.close()
                    else:
                        print("database connection failed.")
                        logger.error("database connection failed when adding student record")
                except Exception as e:
                    print("error adding student record. please try again.")
                    logger.error(f"error in add student record process: {e}")

            elif admin_choice == "7":
                # view grade summary
                try:
                    index_number = input("Enter index number to summarize grades: ").strip()
                    logger.info(f"admin viewing grade summary for student: {index_number}")
                    
                    conn = connect_to_db()
                    if conn:
                        try:
                            student_data = fetch_student_by_index_number(conn, index_number)
                            if student_data:
                                summary = summarize_grades(student_data["grades"])
                                pprint(summary)
                                logger.info(f"displayed grade summary for student: {index_number}")
                            else:
                                print("no records found.")
                                logger.warning(f"no records found for grade summary: {index_number}")
                        finally:
                            conn.close()
                    else:
                        print("connection failed.")
                        logger.error("database connection failed when viewing grade summary")
                except Exception as e:
                    print("error retrieving grade summary. please try again.")
                    logger.error(f"error getting grade summary: {e}")

            elif admin_choice == "8":
                # bulk import student records
                try:
                    logger.info("admin starting bulk import process")
                    print("\n💡 expecting csv/txt file with these headers:")
                    print(", ".join(REQUIRED_FIELDS) + "\n")
                    
                    file_path = input("Enter the path to the CSV/TXT file: ").strip()
                    logger.info(f"admin importing from file: {file_path}")
                    
                    summary = bulk_import_from_file(file_path)
                    
                    print("\n📦 bulk import summary:")
                    print(f"message: {summary['message']}")
                    print(f"total records: {summary['total']}")
                    print(f"successfully imported: {summary['successful']}")
                    print(f"skipped: {summary['skipped']}")
                    
                    if summary['errors']:
                        print("⚠️ errors:")
                        for err in summary['errors']:
                            print(f"- {err}")
                    
                    logger.info(f"bulk import completed: {summary['successful']}/{summary['total']} successful")
                except Exception as e:
                    print("error during bulk import. please try again.")
                    logger.error(f"error in bulk import process: {e}")

            elif admin_choice == "9":
                # Enhanced Course & Semester Management
                print("🎓 Opening Enhanced Management...")
                logger.info("Admin accessing enhanced course & semester management")
                try:
                    # Sub-menu for enhanced features
                    while True:
                        print("\n=== ENHANCED MANAGEMENT ===")
                        print("1. Course Management")
                        print("2. Semester Management") 
                        print("3. Initialize Enhanced System")
                        print("0. Back to Admin Menu")
                        
                        enhanced_choice = input("Choose an option: ").strip()
                        
                        if enhanced_choice == "1":
                            course_management_main()
                        elif enhanced_choice == "2":
                            semester_management_main()
                        elif enhanced_choice == "3":
                            initialize_enhanced_system()
                        elif enhanced_choice == "0":
                            break
                        else:
                            print("Invalid option. Please try again.")
                            
                except Exception as e:
                    print(f"Error in enhanced management: {e}")
                    logger.error(f"Error in enhanced management: {e}")

            elif admin_choice == "10":
                # logout
                print("logging out...")
                logger.info("admin logging out")
                break

            else:
                print("invalid option. please try again.")
                logger.warning(f"invalid admin menu choice: {admin_choice}")
                
        except KeyboardInterrupt:
            print("\n\nreturning to main menu...")
            logger.info("admin menu interrupted by user")
            break
        except Exception as e:
            print("an unexpected error occurred. please try again.")
            logger.error(f"unexpected error in admin menu: {e}")


def run_menu():
    """main menu loop for the application"""
    logger.info("starting main menu loop")
    
    while True:
        try:
            print("\nWelcome to Student Result Management Tool")
            print("1. Login")
            print("2. Sign Up")
            print("3. Exit")
            
            choice = input("Choose an option: ").strip()
            logger.debug(f"user selected main menu option: {choice}")
            
            if choice == "1":
                try:
                    username, role = login()
                    if not username:
                        logger.info("login failed or cancelled")
                        continue
                    
                    logger.info(f"successful login: {username} as {role}")
                    
                    if role == "admin":
                        admin_menu_loop()
                    elif role == "student":
                        show_student_menu(username)
                        
                except Exception as e:
                    print("error during login. please try again.")
                    logger.error(f"login error: {e}")

            elif choice == "2":
                try:
                    sign_up()
                    logger.info("sign up process completed")
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
