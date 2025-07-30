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

Author: SRMS Team
Version: 1.0
"""

from db import (
    connect_to_db,
    create_enhanced_tables,
    insert_course,
    fetch_all_courses,
    fetch_course_by_code,
    update_course,
    delete_course,
    insert_semester,
    fetch_all_semesters,
    fetch_current_semester,
    set_current_semester
)
from logger import get_logger
from datetime import datetime

logger = get_logger(__name__)

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
    """List all available courses"""
    try:
        courses = fetch_all_courses()
        if not courses:
            print("No courses found.")
            return
        
        print(f"\n{'Code':<12} {'Title':<30} {'Credits':<8} {'Department':<15} {'Instructor':<20}")
        print("-" * 85)
        
        for course in courses:
            print(f"{course['course_code']:<12} {course['course_title']:<30} "
                  f"{course['credit_hours']:<8} {course.get('department', 'N/A'):<15} "
                  f"{course.get('instructor', 'N/A'):<20}")
        
        print(f"\nTotal courses: {len(courses)}")
        
    except Exception as e:
        logger.error(f"Error listing courses: {e}")
        print("Error retrieving courses.")

def add_new_course():
    """Add a new course to the system"""
    try:
        print("\n=== ADD NEW COURSE ===")
        
        course_code = input("Course Code (e.g., CS101): ").strip().upper()
        if not course_code:
            print("Course code is required.")
            return
        
        # Check if course already exists
        existing = fetch_course_by_code(course_code)
        if existing:
            print(f"Course {course_code} already exists. Use edit function to modify.")
            return
        
        course_title = input("Course Title: ").strip()
        if not course_title:
            print("Course title is required.")
            return
        
        try:
            credit_hours = int(input("Credit Hours (default 3): ").strip() or "3")
        except ValueError:
            credit_hours = 3
        
        department = input("Department (optional): ").strip() or None
        instructor = input("Instructor (optional): ").strip() or None
        description = input("Description (optional): ").strip() or None
        
        course_data = {
            "course_code": course_code,
            "course_title": course_title,
            "credit_hours": credit_hours,
            "department": department,
            "instructor": instructor,
            "description": description
        }
        
        conn = connect_to_db()
        if not conn:
            print("Database connection failed.")
            return
        
        if insert_course(conn, course_data):
            print(f"Course {course_code} added successfully!")
        else:
            print("Failed to add course.")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"Error adding course: {e}")
        print("Error adding course.")

def edit_course():
    """Edit an existing course"""
    try:
        print("\n=== EDIT COURSE ===")
        
        course_code = input("Enter Course Code to edit: ").strip().upper()
        if not course_code:
            print("Course code is required.")
            return
        
        # Check if course exists
        existing = fetch_course_by_code(course_code)
        if not existing:
            print(f"Course {course_code} not found.")
            return
        
        print(f"\nCurrent course details:")
        print(f"Code: {existing['course_code']}")
        print(f"Title: {existing['course_title']}")
        print(f"Credits: {existing['credit_hours']}")
        print(f"Department: {existing.get('department', 'N/A')}")
        print(f"Instructor: {existing.get('instructor', 'N/A')}")
        print(f"Description: {existing.get('description', 'N/A')}")
        
        print("\nEnter new values (press Enter to keep current value):")
        
        updates = {}
        
        new_title = input(f"Course Title ({existing['course_title']}): ").strip()
        if new_title:
            updates["course_title"] = new_title
        
        new_credits = input(f"Credit Hours ({existing['credit_hours']}): ").strip()
        if new_credits:
            try:
                updates["credit_hours"] = int(new_credits)
            except ValueError:
                print("Invalid credit hours, keeping current value.")
        
        new_dept = input(f"Department ({existing.get('department', 'N/A')}): ").strip()
        if new_dept:
            updates["department"] = new_dept
        
        new_instructor = input(f"Instructor ({existing.get('instructor', 'N/A')}): ").strip()
        if new_instructor:
            updates["instructor"] = new_instructor
        
        new_desc = input(f"Description ({existing.get('description', 'N/A')}): ").strip()
        if new_desc:
            updates["description"] = new_desc
        
        if not updates:
            print("No changes made.")
            return
        
        if update_course(course_code, updates):
            print(f"Course {course_code} updated successfully!")
        else:
            print("Failed to update course.")
        
    except Exception as e:
        logger.error(f"Error editing course: {e}")
        print("Error editing course.")

def delete_course_cli():
    """Delete a course from the system"""
    try:
        print("\n=== DELETE COURSE ===")
        
        course_code = input("Enter Course Code to delete: ").strip().upper()
        if not course_code:
            print("Course code is required.")
            return
        
        # Check if course exists
        existing = fetch_course_by_code(course_code)
        if not existing:
            print(f"Course {course_code} not found.")
            return
        
        print(f"\nCourse to delete:")
        print(f"Code: {existing['course_code']}")
        print(f"Title: {existing['course_title']}")
        
        confirm = input("\nAre you sure you want to delete this course? (yes/no): ").strip().lower()
        if confirm not in ['yes', 'y']:
            print("Course deletion cancelled.")
            return
        
        if delete_course(course_code):
            print(f"Course {course_code} deleted successfully!")
        else:
            print("Failed to delete course.")
        
    except Exception as e:
        logger.error(f"Error deleting course: {e}")
        print("Error deleting course.")

def search_course():
    """Search for a specific course"""
    try:
        print("\n=== SEARCH COURSE ===")
        
        course_code = input("Enter Course Code: ").strip().upper()
        if not course_code:
            print("Course code is required.")
            return
        
        course = fetch_course_by_code(course_code)
        if not course:
            print(f"Course {course_code} not found.")
            return
        
        print(f"\nCourse Details:")
        print(f"Code: {course['course_code']}")
        print(f"Title: {course['course_title']}")
        print(f"Credits: {course['credit_hours']}")
        print(f"Department: {course.get('department', 'N/A')}")
        print(f"Instructor: {course.get('instructor', 'N/A')}")
        print(f"Description: {course.get('description', 'N/A')}")
        print(f"Created: {course.get('created_at', 'N/A')}")
        
    except Exception as e:
        logger.error(f"Error searching course: {e}")
        print("Error searching course.")

def list_all_semesters():
    """List all semesters"""
    try:
        semesters = fetch_all_semesters()
        if not semesters:
            print("No semesters found.")
            return
        
        print(f"\n{'ID':<12} {'Name':<20} {'Academic Year':<15} {'Current':<8} {'Start Date':<12} {'End Date'}")
        print("-" * 75)
        
        for semester in semesters:
            current_mark = "✓" if semester.get('is_current') else ""
            start_date = semester.get('start_date', 'N/A')
            end_date = semester.get('end_date', 'N/A')
            
            print(f"{semester['semester_id']:<12} {semester['semester_name']:<20} "
                  f"{semester['academic_year']:<15} {current_mark:<8} "
                  f"{start_date:<12} {end_date}")
        
        print(f"\nTotal semesters: {len(semesters)}")
        
    except Exception as e:
        logger.error(f"Error listing semesters: {e}")
        print("Error retrieving semesters.")

def add_new_semester():
    """Add a new semester"""
    try:
        print("\n=== ADD NEW SEMESTER ===")
        
        semester_id = input("Semester ID (e.g., FALL2025): ").strip().upper()
        if not semester_id:
            print("Semester ID is required.")
            return
        
        semester_name = input("Semester Name (e.g., Fall 2025): ").strip()
        if not semester_name:
            print("Semester name is required.")
            return
        
        academic_year = input("Academic Year (e.g., 2025-2026): ").strip()
        if not academic_year:
            print("Academic year is required.")
            return
        
        start_date = input("Start Date (YYYY-MM-DD, optional): ").strip() or None
        end_date = input("End Date (YYYY-MM-DD, optional): ").strip() or None
        
        current_input = input("Set as current semester? (y/n): ").strip().lower()
        is_current = current_input in ['y', 'yes']
        
        semester_data = {
            "semester_id": semester_id,
            "semester_name": semester_name,
            "academic_year": academic_year,
            "start_date": start_date,
            "end_date": end_date,
            "is_current": is_current
        }
        
        conn = connect_to_db()
        if not conn:
            print("Database connection failed.")
            return
        
        if insert_semester(conn, semester_data):
            print(f"Semester {semester_id} added successfully!")
        else:
            print("Failed to add semester.")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"Error adding semester: {e}")
        print("Error adding semester.")

def set_current_semester_cli():
    """Set a semester as current"""
    try:
        print("\n=== SET CURRENT SEMESTER ===")
        
        # Show available semesters
        semesters = fetch_all_semesters()
        if not semesters:
            print("No semesters found.")
            return
        
        print("Available semesters:")
        for i, semester in enumerate(semesters, 1):
            current_mark = " (CURRENT)" if semester.get('is_current') else ""
            print(f"{i}. {semester['semester_id']} - {semester['semester_name']}{current_mark}")
        
        try:
            choice = int(input("\nSelect semester number: ")) - 1
            if 0 <= choice < len(semesters):
                selected_semester = semesters[choice]
                
                if set_current_semester(selected_semester['semester_id']):
                    print(f"Semester {selected_semester['semester_id']} set as current!")
                else:
                    print("Failed to set current semester.")
            else:
                print("Invalid selection.")
        except ValueError:
            print("Invalid input.")
        
    except Exception as e:
        logger.error(f"Error setting current semester: {e}")
        print("Error setting current semester.")

def view_current_semester():
    """View the current active semester"""
    try:
        current = fetch_current_semester()
        if not current:
            print("No current semester set.")
            return
        
        print(f"\nCurrent Semester:")
        print(f"ID: {current['semester_id']}")
        print(f"Name: {current['semester_name']}")
        print(f"Academic Year: {current['academic_year']}")
        print(f"Start Date: {current.get('start_date', 'N/A')}")
        print(f"End Date: {current.get('end_date', 'N/A')}")
        
    except Exception as e:
        logger.error(f"Error viewing current semester: {e}")
        print("Error retrieving current semester.")

def initialize_enhanced_system():
    """Initialize the enhanced database tables"""
    try:
        print("\n=== INITIALIZING ENHANCED SYSTEM ===")
        print("Creating enhanced database tables...")
        
        if create_enhanced_tables():
            print("Enhanced tables initialized successfully!")
            print("\nThe following tables were created/verified:")
            print("- courses (course management)")
            print("- semesters (academic calendar)")
            print("- assessments (detailed grade tracking)")
            print("- enrollments (student-course relationships)")
            print("\nYou can now use the enhanced course and semester management features.")
        else:
            print("Failed to initialize enhanced tables.")
        
    except Exception as e:
        logger.error(f"Error initializing enhanced system: {e}")
        print("Error initializing enhanced system.")

def course_management_main():
    """Main course management function"""
    while True:
        choice = display_courses_menu()
        
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
        else:
            print("Invalid option. Please try again.")
        
        input("\nPress Enter to continue...")

def semester_management_main():
    """Main semester management function"""
    while True:
        choice = display_semesters_menu()
        
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
        else:
            print("Invalid option. Please try again.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    print("Course Management Module")
    print("This module should be imported and used by the main menu system.")
