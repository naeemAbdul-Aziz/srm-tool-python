#!/usr/bin/env python3
"""
comprehensive_seed.py - Comprehensive University of Ghana Database Seeding
==========================================================================

This script creates a complete, realistic dataset for the Student Result Management System
with authentic University of Ghana data including:
- Multiple academic years and semesters
- Diverse student profiles across different programs
- Comprehensive course catalog with proper UG course codes
- Realistic grade distributions and academic progression
- Complete user accounts with proper authentication

Usage: python comprehensive_seed.py
"""

import random
from datetime import datetime, date, timedelta
from db import (
    connect_to_db, create_tables_if_not_exist, insert_student_profile, 
    insert_course, insert_semester, insert_grade, fetch_semester_by_name,
    fetch_course_by_code, fetch_student_by_index_number
)
from auth import create_student_account, create_user
from logger import get_logger

logger = get_logger(__name__)

# ========================================
# UNIVERSITY OF GHANA DATA CONSTANTS
# ========================================

# Authentic Ghanaian Names
GHANAIAN_MALE_NAMES = [
    "Kwame", "Kofi", "Kwaku", "Yaw", "Kwadwo", "Kwabena", "Kwesi", "Akwasi",
    "Nana", "Kojo", "Fiifi", "Ato", "Ebo", "Kodwo", "Paa", "Ekow",
    "Nii", "Tetteh", "Lartey", "Adjei", "Richmond", "Emmanuel", "Samuel",
    "Daniel", "Michael", "David", "Joseph", "Francis", "Prince", "Felix",
    "Eric", "Justice", "Bright", "Isaac", "Abraham", "Moses", "John",
    "Godfred", "Benjamin", "Stephen", "Mark", "Paul", "James", "Peter"
]

GHANAIAN_FEMALE_NAMES = [
    "Ama", "Efua", "Akua", "Yaa", "Adwoa", "Abena", "Esi", "Akosua",
    "Adjoa", "Afua", "Afia", "Akoto", "Nana", "Akorfa", "Dzidzor", "Edem",
    "Vivian", "Grace", "Patience", "Mercy", "Comfort", "Charity", "Faith",
    "Joyce", "Linda", "Sandra", "Patricia", "Gifty", "Vida", "Faustina",
    "Joana", "Priscilla", "Gloria", "Eunice", "Rose", "Mary", "Elizabeth",
    "Portia", "Hannah", "Ruth", "Esther", "Deborah", "Sarah", "Rebecca"
]

GHANAIAN_SURNAMES = [
    "Asante", "Mensah", "Osei", "Boateng", "Owusu", "Agyei", "Adjei", "Frimpong",
    "Opoku", "Gyasi", "Nkrumah", "Danso", "Amponsah", "Bediako", "Ofori",
    "Acheampong", "Antwi", "Darko", "Amoah", "Akoto", "Preko", "Sarfo",
    "Tetteh", "Lartey", "Nii", "Okine", "Quartey", "Addo", "Lamptey",
    "Koomson", "Quaye", "Bruce", "Ankrah", "Tagoe", "Nortey", "Ashong",
    "Ablakwa", "Agbodza", "Amankwah", "Appiah", "Kusi", "Yeboah", "Kyei",
    "Ntim", "Okyere", "Kwarteng", "Donkor", "Asamoah", "Akufo", "Addai",
    "Bonsu", "Duah", "Wiredu", "Ampofo", "Baah", "Nyong", "Obeng"
]

# University of Ghana Schools and Programs
UG_SCHOOLS_AND_PROGRAMS = {
    "College of Basic and Applied Sciences": [
        "Computer Science", "Information Technology", "Statistics", "Mathematics",
        "Physics", "Chemistry", "Biology", "Biochemistry", "Biotechnology",
        "Food Science and Nutrition", "Agricultural Science", "Animal Science"
    ],
    "College of Health Sciences": [
        "Medicine", "Nursing", "Pharmacy", "Dentistry", "Public Health",
        "Medical Laboratory Sciences", "Physiotherapy", "Radiography"
    ],
    "College of Humanities": [
        "English Language", "Linguistics", "French", "Philosophy", "Music",
        "Theatre Arts", "Fine Arts", "Dance Studies", "Religious Studies",
        "Arabic and Islamic Studies", "Modern Languages"
    ],
    "College of Education": [
        "Educational Administration", "Educational Psychology", "Curriculum Studies",
        "Educational Foundations", "Science Education", "Mathematics Education",
        "ICT Education", "Technical Education"
    ],
    "Legon Business School": [
        "Business Administration", "Accounting", "Finance", "Marketing",
        "Human Resource Management", "Supply Chain Management", "Entrepreneurship"
    ],
    "School of Law": [
        "Law"
    ],
    "School of Social Sciences": [
        "Economics", "Political Science", "Sociology", "Geography", "History",
        "Psychology", "Social Work", "International Affairs", "African Studies"
    ]
}

# Comprehensive University of Ghana Course Catalog
UG_COMPREHENSIVE_COURSES = [
    # Computer Science & IT (UGCS/UGIT)
    ("UGCS101", "Introduction to Computing", 3),
    ("UGCS102", "Programming Fundamentals", 3),
    ("UGCS201", "Data Structures and Algorithms", 3),
    ("UGCS202", "Computer Architecture", 3),
    ("UGCS301", "Database Systems", 3),
    ("UGCS302", "Software Engineering", 3),
    ("UGCS303", "Operating Systems", 3),
    ("UGCS401", "Computer Networks", 3),
    ("UGCS402", "Artificial Intelligence", 3),
    ("UGCS403", "Machine Learning", 3),
    ("UGIT201", "Web Development", 3),
    ("UGIT301", "Mobile App Development", 3),
    ("UGIT302", "Systems Analysis and Design", 3),
    ("UGIT401", "IT Project Management", 3),
    
    # Mathematics & Statistics (UGMA/UGST)
    ("UGMA101", "Calculus I", 3),
    ("UGMA102", "Algebra and Trigonometry", 3),
    ("UGMA201", "Linear Algebra", 3),
    ("UGMA202", "Calculus II", 3),
    ("UGMA301", "Real Analysis", 3),
    ("UGMA302", "Abstract Algebra", 3),
    ("UGMA401", "Complex Analysis", 3),
    ("UGST201", "Statistical Methods", 3),
    ("UGST202", "Probability Theory", 3),
    ("UGST301", "Applied Statistics", 3),
    ("UGST302", "Statistical Inference", 3),
    ("UGST401", "Multivariate Statistics", 3),
    
    # Sciences (UGPH/UGCH/UGBI)
    ("UGPH101", "General Physics I", 3),
    ("UGPH102", "General Physics II", 3),
    ("UGPH201", "Classical Mechanics", 3),
    ("UGPH202", "Electromagnetism", 3),
    ("UGPH301", "Quantum Physics", 3),
    ("UGPH302", "Thermodynamics", 3),
    ("UGCH101", "General Chemistry I", 3),
    ("UGCH102", "General Chemistry II", 3),
    ("UGCH201", "Organic Chemistry I", 3),
    ("UGCH202", "Organic Chemistry II", 3),
    ("UGCH301", "Physical Chemistry", 3),
    ("UGCH302", "Analytical Chemistry", 3),
    ("UGBI101", "General Biology", 3),
    ("UGBI201", "Cell Biology", 3),
    ("UGBI202", "Genetics", 3),
    ("UGBI301", "Ecology", 3),
    ("UGBI302", "Molecular Biology", 3),
    ("UGBI401", "Biotechnology", 3),
    
    # Business & Economics (UGBA/UGEC)
    ("UGEC101", "Principles of Economics", 3),
    ("UGEC102", "Introduction to Business", 3),
    ("UGEC201", "Microeconomics", 3),
    ("UGEC202", "Macroeconomics", 3),
    ("UGEC301", "International Economics", 3),
    ("UGEC302", "Development Economics", 3),
    ("UGEC401", "Econometrics", 3),
    ("UGBA201", "Financial Accounting", 3),
    ("UGBA202", "Management Accounting", 3),
    ("UGBA301", "Corporate Finance", 3),
    ("UGBA302", "Marketing Management", 3),
    ("UGBA401", "Strategic Management", 3),
    ("UGBA402", "Operations Management", 3),
    
    # Social Sciences (UGPS/UGSO/UGHI/UGPY)
    ("UGPS101", "Introduction to Political Science", 3),
    ("UGPS201", "Comparative Politics", 3),
    ("UGPS202", "International Relations", 3),
    ("UGPS301", "Public Administration", 3),
    ("UGPS302", "Political Theory", 3),
    ("UGPS401", "African Politics", 3),
    ("UGSO201", "Social Research Methods", 3),
    ("UGSO202", "Social Theory", 3),
    ("UGSO301", "Development Sociology", 3),
    ("UGSO302", "Urban Sociology", 3),
    ("UGSO401", "Gender Studies", 3),
    ("UGHI201", "History of Ghana", 3),
    ("UGHI202", "World History", 3),
    ("UGHI301", "African History", 3),
    ("UGHI302", "Colonial History", 3),
    ("UGHI401", "Historiography", 3),
    ("UGPY201", "General Psychology", 3),
    ("UGPY202", "Developmental Psychology", 3),
    ("UGPY301", "Social Psychology", 3),
    ("UGPY302", "Cognitive Psychology", 3),
    
    # Languages & Literature (UGEN/UGFR/UGMU)
    ("UGEN101", "Academic Writing", 3),
    ("UGEN102", "Literature in English", 3),
    ("UGEN201", "African Literature", 3),
    ("UGEN202", "Creative Writing", 3),
    ("UGEN301", "Linguistics", 3),
    ("UGEN302", "Language and Society", 3),
    ("UGFR101", "Elementary French", 3),
    ("UGFR102", "French Grammar", 3),
    ("UGFR201", "Intermediate French", 3),
    ("UGFR202", "French Literature", 3),
    ("UGMU201", "Music Theory", 3),
    ("UGMU202", "African Music", 3),
    ("UGMU301", "Music Composition", 3),
    
    # General/Core Courses (UGCO)
    ("UGCO101", "Critical Thinking", 2),
    ("UGCO102", "Communication Skills", 2),
    ("UGCO103", "Introduction to University Studies", 1),
    ("UGCO201", "African Studies", 2),
    ("UGCO202", "Philosophy and Logic", 2),
    ("UGCO203", "Environmental Studies", 2),
    ("UGCO301", "Research Methods", 3),
    ("UGCO302", "Ethics and Values", 2),
    ("UGCO401", "Project Work", 6),
    ("UGCO402", "Entrepreneurship", 2),
    
    # Health Sciences (UGMD/UGNU/UGPH)
    ("UGMD101", "Medical Terminology", 2),
    ("UGMD201", "Human Anatomy", 4),
    ("UGMD202", "Human Physiology", 4),
    ("UGMD301", "Pathology", 4),
    ("UGMD302", "Pharmacology", 3),
    ("UGMD401", "Clinical Medicine", 6),
    ("UGNU201", "Fundamentals of Nursing", 3),
    ("UGNU202", "Health Assessment", 3),
    ("UGNU301", "Medical-Surgical Nursing", 4),
    ("UGNU302", "Community Health Nursing", 3),
    ("UGPH301", "Clinical Pharmacy", 4),
    ("UGPH302", "Pharmaceutical Chemistry", 3),
    
    # Law (UGLAW)
    ("UGLAW101", "Introduction to Law", 3),
    ("UGLAW201", "Constitutional Law", 3),
    ("UGLAW202", "Contract Law", 3),
    ("UGLAW301", "Criminal Law", 3),
    ("UGLAW302", "Property Law", 3),
    ("UGLAW401", "International Law", 3),
    
    # Engineering (UGCE/UGEE/UGME)
    ("UGCE101", "Engineering Mathematics I", 3),
    ("UGCE102", "Engineering Drawing", 2),
    ("UGCE201", "Engineering Mathematics II", 3),
    ("UGCE202", "Mechanics of Materials", 3),
    ("UGCE301", "Structural Analysis", 3),
    ("UGCE302", "Concrete Technology", 3),
    ("UGEE201", "Circuit Analysis", 3),
    ("UGEE202", "Electronics", 3),
    ("UGEE301", "Power Systems", 3),
    ("UGEE302", "Control Systems", 3),
    ("UGME201", "Thermodynamics", 3),
    ("UGME202", "Fluid Mechanics", 3),
    ("UGME301", "Machine Design", 3),
    ("UGME302", "Manufacturing Processes", 3)
]

# Academic Semesters for University of Ghana
UG_ACADEMIC_CALENDAR = [
    ("1st Semester 2021/2022", "2021/2022", date(2021, 8, 16), date(2021, 12, 17)),
    ("2nd Semester 2021/2022", "2021/2022", date(2022, 1, 17), date(2022, 5, 20)),
    ("1st Semester 2022/2023", "2022/2023", date(2022, 8, 15), date(2022, 12, 16)),
    ("2nd Semester 2022/2023", "2022/2023", date(2023, 1, 16), date(2023, 5, 19)),
    ("1st Semester 2023/2024", "2023/2024", date(2023, 8, 14), date(2023, 12, 15)),
    ("2nd Semester 2023/2024", "2023/2024", date(2024, 1, 15), date(2024, 5, 17)),
    ("1st Semester 2024/2025", "2024/2025", date(2024, 8, 12), date(2024, 12, 13)),
    ("2nd Semester 2024/2025", "2024/2025", date(2025, 1, 13), date(2025, 5, 16))
]

# ========================================
# HELPER FUNCTIONS
# ========================================

def generate_ug_index(student_number):
    """Generate UG index number: ug + 5 digits"""
    return f"ug{str(student_number).zfill(5)}"

def generate_ug_email(first_name, last_name, index_number):
    """Generate UG email address"""
    if random.choice([True, False]):
        return f"{first_name.lower()}.{last_name.lower()}@st.ug.edu.gh"
    else:
        return f"{index_number}@st.ug.edu.gh"

def generate_ghana_phone():
    """Generate Ghanaian mobile number"""
    networks = ["24", "26", "27", "28", "50", "54", "55", "59"]  # Major networks
    network = random.choice(networks)
    number = random.randint(1000000, 9999999)
    return f"+233{network}{number}"

def get_realistic_birth_date(year_of_study, current_year=2025):
    """Generate realistic birth date for university student"""
    typical_age = 18 + (year_of_study - 1) + random.randint(0, 2)  # 18-25 range
    birth_year = current_year - typical_age
    birth_month = random.randint(1, 12)
    birth_day = random.randint(1, 28)
    return date(birth_year, birth_month, birth_day)

def get_program_for_school(school):
    """Get random program from specified school"""
    return random.choice(UG_SCHOOLS_AND_PROGRAMS[school])

def get_courses_for_program_and_year(program, year_of_study):
    """Get appropriate courses for program and year"""
    courses = []
    
    # Core courses for all students
    if year_of_study == 1:
        core_1st = [c for c in UG_COMPREHENSIVE_COURSES if c[0].startswith("UGCO1")]
        courses.extend(random.sample(core_1st, min(3, len(core_1st))))
    elif year_of_study == 2:
        core_2nd = [c for c in UG_COMPREHENSIVE_COURSES if c[0].startswith("UGCO2")]
        courses.extend(random.sample(core_2nd, min(2, len(core_2nd))))
    elif year_of_study >= 3:
        core_upper = [c for c in UG_COMPREHENSIVE_COURSES if c[0].startswith("UGCO3") or c[0].startswith("UGCO4")]
        courses.extend(random.sample(core_upper, min(2, len(core_upper))))
    
    # Program-specific courses
    program_courses = []
    year_level = str(year_of_study)
    
    if "Computer Science" in program or "Information Technology" in program:
        program_courses = [c for c in UG_COMPREHENSIVE_COURSES if c[0].startswith(("UGCS", "UGIT", "UGMA")) and year_level in c[0]]
    elif "Business" in program or "Economics" in program or "Accounting" in program or "Finance" in program:
        program_courses = [c for c in UG_COMPREHENSIVE_COURSES if c[0].startswith(("UGBA", "UGEC")) and year_level in c[0]]
    elif "Mathematics" in program or "Statistics" in program:
        program_courses = [c for c in UG_COMPREHENSIVE_COURSES if c[0].startswith(("UGMA", "UGST")) and year_level in c[0]]
    elif "Medicine" in program or "Nursing" in program or "Pharmacy" in program:
        program_courses = [c for c in UG_COMPREHENSIVE_COURSES if c[0].startswith(("UGMD", "UGNU", "UGPH")) and year_level in c[0]]
    elif "Physics" in program or "Chemistry" in program or "Biology" in program:
        program_courses = [c for c in UG_COMPREHENSIVE_COURSES if c[0].startswith(("UGPH", "UGCH", "UGBI")) and year_level in c[0]]
    elif "Law" in program:
        program_courses = [c for c in UG_COMPREHENSIVE_COURSES if c[0].startswith("UGLAW") and year_level in c[0]]
    elif "Engineering" in program:
        program_courses = [c for c in UG_COMPREHENSIVE_COURSES if c[0].startswith(("UGCE", "UGEE", "UGME")) and year_level in c[0]]
    else:  # Social Sciences, Humanities
        program_courses = [c for c in UG_COMPREHENSIVE_COURSES if c[0].startswith(("UGPS", "UGSO", "UGHI", "UGEN", "UGPY")) and year_level in c[0]]
    
    # Add 4-6 program courses
    if program_courses:
        courses.extend(random.sample(program_courses, min(random.randint(4, 6), len(program_courses))))
    
    # Add some general/elective courses
    general_courses = [c for c in UG_COMPREHENSIVE_COURSES if c[0].startswith(("UGEN", "UGFR")) and year_level in c[0]]
    if general_courses and len(courses) < 8:
        courses.extend(random.sample(general_courses, min(2, len(general_courses))))
    
    return courses[:8]  # Limit to 8 courses per semester

def generate_realistic_grade(year_of_study, course_code, student_ability="average"):
    """Generate realistic grades based on year, course difficulty, and student ability"""
    # Base performance by year (students generally improve over time)
    year_bonus = {1: 0, 2: 3, 3: 5, 4: 7}
    base_score = 60 + year_bonus.get(year_of_study, 0)
    
    # Course difficulty adjustment
    if any(level in course_code for level in ["401", "402", "403", "404"]):  # Final year courses
        base_score -= 8
    elif any(level in course_code for level in ["301", "302", "303"]):  # Third year
        base_score -= 4
    elif any(level in course_code for level in ["101", "102", "103"]):  # First year
        base_score += 5
    
    # Student ability adjustment
    ability_modifier = {"weak": -10, "average": 0, "strong": 10, "excellent": 15}
    base_score += ability_modifier.get(student_ability, 0)
    
    # Add random variation (normal distribution)
    final_score = random.normalvariate(base_score, 12)
    
    # Ensure realistic bounds
    return max(30, min(100, round(final_score, 1)))

# ========================================
# MAIN SEEDING FUNCTIONS
# ========================================

def seed_comprehensive_courses(conn):
    """Seed all University of Ghana courses"""
    logger.info("COURSES: Seeding comprehensive UG course catalog...")
    success_count = 0
    
    for course_code, course_title, credit_hours in UG_COMPREHENSIVE_COURSES:
        try:
            if insert_course(conn, course_code, course_title, credit_hours):
                success_count += 1
                logger.debug(f"Added course: {course_code} - {course_title}")
        except Exception as e:
            logger.warning(f"Course {course_code} may already exist: {e}")
    
    logger.info(f"SUCCESS: Successfully seeded {success_count}/{len(UG_COMPREHENSIVE_COURSES)} courses")
    return success_count

def seed_academic_calendar(conn):
    """Seed University of Ghana academic calendar"""
    logger.info("CALENDAR: Seeding UG academic calendar...")
    semester_ids = {}
    success_count = 0
    
    for semester_name, academic_year, start_date, end_date in UG_ACADEMIC_CALENDAR:
        try:
            # Fix parameter order: semester_name, start_date, end_date, academic_year
            semester_id = insert_semester(conn, semester_name, start_date, end_date, academic_year)
            if semester_id:
                semester_ids[semester_name] = semester_id
                success_count += 1
                logger.debug(f"Added semester: {semester_name}")
        except Exception as e:
            logger.warning(f"Semester {semester_name} may already exist: {e}")
    
    logger.info(f"SUCCESS: Successfully seeded {success_count}/{len(UG_ACADEMIC_CALENDAR)} semesters")
    return semester_ids

def seed_diverse_students(conn, num_students=100):
    """Seed diverse student population across all UG schools"""
    logger.info(f"STUDENTS: Seeding {num_students} diverse UG students...")
    
    students_data = []
    student_ids = {}
    
    # Distribute students across schools proportionally
    school_distribution = {
        "College of Basic and Applied Sciences": 0.25,
        "College of Health Sciences": 0.15,
        "College of Humanities": 0.15,
        "College of Education": 0.10,
        "Legon Business School": 0.20,
        "School of Law": 0.05,
        "School of Social Sciences": 0.10
    }
    
    student_counter = 1
    
    for school, proportion in school_distribution.items():
        school_student_count = int(num_students * proportion)
        
        for i in range(school_student_count):
            # Generate student demographics
            gender = random.choice(["Male", "Female"])
            first_name = random.choice(GHANAIAN_MALE_NAMES if gender == "Male" else GHANAIAN_FEMALE_NAMES)
            last_name = random.choice(GHANAIAN_SURNAMES)
            full_name = f"{first_name} {last_name}"
            
            # Academic details
            year_of_study = random.randint(1, 4)
            program = get_program_for_school(school)
            index_number = generate_ug_index(10000 + student_counter)
            
            # Personal details
            birth_date = get_realistic_birth_date(year_of_study)
            email = generate_ug_email(first_name, last_name, index_number)
            phone = generate_ghana_phone()
            
            # Student ability level (affects grades)
            ability = random.choices(
                ["weak", "average", "strong", "excellent"],
                weights=[15, 50, 25, 10]  # Realistic distribution
            )[0]
            
            student_data = {
                "index_number": index_number,
                "full_name": full_name,
                "first_name": first_name,
                "birth_date": birth_date,
                "gender": gender,
                "email": email,
                "phone": phone,
                "program": program,
                "school": school,
                "year_of_study": year_of_study,
                "ability": ability
            }
            
            students_data.append(student_data)
            student_counter += 1
    
    # Insert students into database
    success_count = 0
    for student in students_data:
        try:
            student_id = insert_student_profile(
                conn,
                student["index_number"],
                student["full_name"],
                student["birth_date"],
                student["gender"],
                student["email"],
                student["phone"],
                student["program"],
                student["year_of_study"]
            )
            
            if student_id:
                student_ids[student["index_number"]] = {
                    "student_id": student_id,
                    "data": student
                }
                success_count += 1
                logger.debug(f"Added student: {student['full_name']} ({student['index_number']})")
                
                # Create user account (since student profile already exists, create user account directly)
                try:
                    index_number = student["index_number"]
                    # Generate default password: last 4 digits + "2024"
                    password = index_number[-4:] + "2024"
                    
                    # Create user account directly using create_user
                    if create_user(index_number, password, 'student'):
                        logger.debug(f"Created user account for {index_number}: {password}")
                    else:
                        logger.warning(f"Failed to create user account for {index_number}")
                except Exception as e:
                    logger.warning(f"Failed to create user account for {student['index_number']}: {e}")
                    
        except Exception as e:
            logger.warning(f"Failed to insert student {student['index_number']}: {e}")
    
    logger.info(f"SUCCESS: Successfully seeded {success_count}/{len(students_data)} students")
    return student_ids

def seed_comprehensive_grades(conn, student_ids, semester_ids):
    """Seed comprehensive grades for all students across multiple semesters"""
    logger.info("GRADES: Seeding comprehensive grade records...")
    
    grade_count = 0
    semester_list = list(UG_ACADEMIC_CALENDAR)
    
    for index_number, student_info in student_ids.items():
        student_id = student_info["student_id"]
        student_data = student_info["data"]
        year_of_study = student_data["year_of_study"]
        program = student_data["program"]
        ability = student_data["ability"]
        
        # Determine which semesters this student should have grades
        # Students have grades for all previous years plus current year
        semesters_to_grade = []
        
        # Add semesters based on year of study
        if year_of_study >= 1:
            semesters_to_grade.extend(["1st Semester 2021/2022", "2nd Semester 2021/2022"])
        if year_of_study >= 2:
            semesters_to_grade.extend(["1st Semester 2022/2023", "2nd Semester 2022/2023"])
        if year_of_study >= 3:
            semesters_to_grade.extend(["1st Semester 2023/2024", "2nd Semester 2023/2024"])
        if year_of_study >= 4:
            semesters_to_grade.extend(["1st Semester 2024/2025"])
        
        # Current semester for all students
        if "2nd Semester 2024/2025" not in semesters_to_grade:
            semesters_to_grade.append("2nd Semester 2024/2025")
        
        # Grade student for each semester
        for semester_name in semesters_to_grade:
            if semester_name not in semester_ids:
                continue
                
            semester_id = semester_ids[semester_name]
            academic_year = semester_name.split()[-1]
            
            # Determine what year level courses to take
            semester_year_level = year_of_study
            if "2021/2022" in semester_name:
                semester_year_level = max(1, year_of_study - 3)
            elif "2022/2023" in semester_name:
                semester_year_level = max(1, year_of_study - 2)
            elif "2023/2024" in semester_name:
                semester_year_level = max(1, year_of_study - 1)
            
            # Get courses for this program and year level
            semester_courses = get_courses_for_program_and_year(program, semester_year_level)
            
            # Add grades for each course
            for course_code, course_title, credit_hours in semester_courses:
                try:
                    # Get course_id from database
                    cursor = conn.cursor()
                    cursor.execute("SELECT course_id FROM courses WHERE course_code = %s", (course_code,))
                    course_result = cursor.fetchone()
                    
                    if course_result:
                        course_id = course_result[0]
                        
                        # Generate realistic score
                        score = generate_realistic_grade(semester_year_level, course_code, ability)
                        
                        # Calculate grade and grade point
                        from grade_util import calculate_grade, get_grade_point
                        grade = calculate_grade(score)
                        grade_point = get_grade_point(score)
                        
                        # Insert grade
                        grade_id = insert_grade(
                            conn,
                            student_id,
                            course_id,
                            semester_id,
                            score,
                            grade,
                            grade_point,
                            academic_year
                        )
                        
                        if grade_id:
                            grade_count += 1
                            logger.debug(f"Added grade: {index_number} - {course_code}: {score}")
                            
                except Exception as e:
                    logger.warning(f"Failed to add grade for {index_number} in {course_code}: {e}")
    
    logger.info(f"SUCCESS: Successfully seeded {grade_count} grade records")
    return grade_count

def create_admin_accounts(conn):
    """Create default admin accounts"""
    logger.info("ADMIN: Creating admin accounts...")
    
    admin_accounts = [
        ("admin", "admin123", "admin"),
        ("registrar", "registrar123", "admin"),
        ("dean", "dean123", "admin")
    ]
    
    success_count = 0
    for username, password, role in admin_accounts:
        try:
            if create_user(username, password, role):
                success_count += 1
                logger.info(f"Created admin account: {username}")
        except Exception as e:
            logger.warning(f"Admin account {username} may already exist: {e}")
    
    logger.info(f"SUCCESS: Successfully created {success_count}/{len(admin_accounts)} admin accounts")
    return success_count

# ========================================
# DATABASE CLEANUP FUNCTIONS
# ========================================

def cleanup_existing_data(conn):
    """Clean up existing data to avoid conflicts"""
    logger.info("CLEANUP: Removing existing data to avoid conflicts...")
    
    try:
        with conn.cursor() as cursor:
            # Delete in reverse dependency order
            cursor.execute("DELETE FROM grades;")
            cursor.execute("DELETE FROM assessments;")
            cursor.execute("DELETE FROM student_profiles;")
            cursor.execute("DELETE FROM semesters;")
            cursor.execute("DELETE FROM courses;")
            cursor.execute("DELETE FROM users WHERE role = 'student';")
            conn.commit()
            logger.info("SUCCESS: Existing data cleaned up")
            return True
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        conn.rollback()
        return False

# ========================================
# MAIN EXECUTION FUNCTION
# ========================================

def seed_comprehensive_database(num_students=100, cleanup_first=True):
    """Main function to seed comprehensive University of Ghana database"""
    try:
        print("UNIVERSITY OF GHANA COMPREHENSIVE DATABASE SEEDING")
        print("=" * 60)
        logger.info("Starting comprehensive database seeding...")
        
        # Connect to database
        conn = connect_to_db()
        if not conn:
            logger.error("Failed to connect to database")
            return False
        
        # Clean up existing data if requested
        if cleanup_first:
            print("CLEANUP: Removing existing data...")
            if not cleanup_existing_data(conn):
                logger.error("Failed to cleanup existing data")
                return False
            print("SUCCESS: Cleanup completed")
        
        # Create tables
        logger.info("TABLES: Creating database tables...")
        create_tables_if_not_exist(conn)
        print("SUCCESS: Database schema ready")
        
        # Seed courses
        course_count = seed_comprehensive_courses(conn)
        print(f"SUCCESS: Courses seeded: {course_count}")
        
        # Seed academic calendar
        semester_ids = seed_academic_calendar(conn)
        print(f"SUCCESS: Semesters seeded: {len(semester_ids)}")
        
        # Create admin accounts
        admin_count = create_admin_accounts(conn)
        print(f"SUCCESS: Admin accounts created: {admin_count}")
        
        # Seed students
        student_ids = seed_diverse_students(conn, num_students)
        print(f"SUCCESS: Students seeded: {len(student_ids)}")
        
        # Seed grades
        grade_count = seed_comprehensive_grades(conn, student_ids, semester_ids)
        print(f"SUCCESS: Grades seeded: {grade_count}")
        
        conn.close()
        
        # Final summary
        print("\n" + "=" * 60)
        print("COMPREHENSIVE SEEDING COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"SUMMARY:")
        print(f"   Courses: {course_count}")
        print(f"   Semesters: {len(semester_ids)}")
        print(f"   Admin accounts: {admin_count}")
        print(f"   Students: {len(student_ids)}")
        print(f"   Grade records: {grade_count}")
        print(f"   Schools represented: {len(UG_SCHOOLS_AND_PROGRAMS)}")
        print("=" * 60)
        
        # Sample login credentials
        print("\nSAMPLE LOGIN CREDENTIALS:")
        print("Admin Login:")
        print("  Username: admin | Password: admin123")
        print("  Username: registrar | Password: registrar123")
        print("\nStudent Login Examples:")
        sample_students = list(student_ids.keys())[:5]
        for index in sample_students:
            password = index[-4:] + "2024"  # Last 4 digits + 2024
            student_name = student_ids[index]["data"]["full_name"]
            print(f"  {index} | {password} | {student_name}")
        
        print(f"\nTotal Students: {len(student_ids)} (use format: ug##### | ####2024)")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"Error during comprehensive seeding: {e}")
        print(f"ERROR: Seeding failed: {e}")
        return False

if __name__ == "__main__":
    print("University of Ghana Comprehensive Database Seeding")
    print("This will create a complete academic dataset with:")
    print("• 130+ courses across all UG schools")
    print("• 8 academic semesters (2021-2025)")
    print("• 100 diverse students with realistic profiles")
    print("• Comprehensive grade records")
    print("• Multiple admin accounts")
    print()
    
    # Ask about cleanup
    cleanup = input("Clean up existing data first? (Y/n): ").strip().lower()
    cleanup_first = cleanup != 'n'
    
    num_students = input("Enter number of students to create (default 100): ").strip()
    if not num_students:
        num_students = 100
    else:
        try:
            num_students = int(num_students)
        except ValueError:
            num_students = 100
    
    confirm = input(f"Proceed with seeding {num_students} students? (y/N): ")
    if confirm.lower() in ['y', 'yes']:
        success = seed_comprehensive_database(num_students, cleanup_first)
        if success:
            print("\nSUCCESS: Database seeding completed successfully!")
            print("You can now use the full system with comprehensive UG data.")
        else:
            print("\nERROR: Database seeding failed. Check logs for details.")
    else:
        print("Operation cancelled.")
