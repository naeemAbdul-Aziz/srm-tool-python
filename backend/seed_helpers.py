"""Helper functions for seeding logic (generation + ensure operations).

Separating generation logic from orchestration allows reuse and unit testing.
"""
import random
from datetime import date
from typing import Optional, Dict, Tuple, List
try:
    from .db import (
        insert_course, insert_semester, insert_student_profile, insert_grade,
    )
    from .grade_util import calculate_grade, get_grade_point
    from .logger import get_logger
    from .seed_constants import (
        GHANAIAN_MALE_NAMES, GHANAIAN_FEMALE_NAMES, GHANAIAN_SURNAMES,
        UG_SCHOOLS_AND_PROGRAMS, UG_COMPREHENSIVE_COURSES
    )
except ImportError:
    from db import (
        insert_course, insert_semester, insert_student_profile, insert_grade,
    )
    from grade_util import calculate_grade, get_grade_point
    from logger import get_logger
    from seed_constants import (
        GHANAIAN_MALE_NAMES, GHANAIAN_FEMALE_NAMES, GHANAIAN_SURNAMES,
        UG_SCHOOLS_AND_PROGRAMS, UG_COMPREHENSIVE_COURSES
    )

logger = get_logger(__name__)

# -----------------
# Generation helpers
# -----------------

def generate_index(number: int) -> str:
    return f"ug{str(number).zfill(5)}"

def generate_email(first: str, last: str, index: str) -> str:
    if random.choice([True, False]):
        return f"{first.lower()}.{last.lower()}@st.ug.edu.gh"
    return f"{index}@st.ug.edu.gh"

def generate_phone() -> str:
    networks = ["24", "26", "27", "28", "50", "54", "55", "59"]
    return f"+233{random.choice(networks)}{random.randint(1000000, 9999999)}"

def generate_birth_date(year_of_study: int, current_year: int = 2025) -> date:
    typical_age = 18 + (year_of_study - 1) + random.randint(0, 2)
    birth_year = current_year - typical_age
    return date(birth_year, random.randint(1, 12), random.randint(1, 28))

def pick_program(school: str) -> str:
    return random.choice(UG_SCHOOLS_AND_PROGRAMS[school])

def select_courses(program: str, year_of_study: int) -> List[Tuple[str,str,int]]:
    courses: List[Tuple[str,str,int]] = []
    yl = str(year_of_study)
    # Simple heuristic selection: choose up to 6 relevant + 2 general
    relevant = [c for c in UG_COMPREHENSIVE_COURSES if yl in c[0]]
    random.shuffle(relevant)
    courses.extend(relevant[:6])
    general = [c for c in UG_COMPREHENSIVE_COURSES if c[0].startswith("UGEN") and yl in c[0]]
    random.shuffle(general)
    courses.extend(general[:2])
    return courses[:8]

def generate_score(year_level: int, course_code: str, ability: str = "average") -> float:
    year_bonus = {1: 0, 2: 3, 3: 5, 4: 7}
    base = 60 + year_bonus.get(year_level, 0)
    if any(lvl in course_code for lvl in ["401", "402", "403", "404"]):
        base -= 8
    elif any(lvl in course_code for lvl in ["301", "302", "303"]):
        base -= 4
    elif any(lvl in course_code for lvl in ["101", "102", "103"]):
        base += 5
    ability_mod = {"weak": -10, "average": 0, "strong": 10, "excellent": 15}
    base += ability_mod.get(ability, 0)
    final = random.normalvariate(base, 12)
    return max(30, min(100, round(final, 1)))

# -----------------
# Ensure helpers
# -----------------

def ensure_course(conn, code: str, title: str, credits: int):
    from psycopg2.extras import RealDictCursor
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT course_id FROM courses WHERE course_code=%s", (code,))
        row = cur.fetchone()
        if row:
            return row["course_id"]
    return insert_course(conn, code, title, credits)

def ensure_semester(conn, semester_name: str, start_date: date, end_date: date, academic_year: Optional[str]):
    from psycopg2.extras import RealDictCursor
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT semester_id FROM semesters WHERE semester_name=%s", (semester_name,))
        row = cur.fetchone()
        if row:
            return row["semester_id"]
    return insert_semester(conn, semester_name, start_date, end_date, academic_year)

def ensure_student(conn, index_number: str, full_name: str, dob: date, gender: str,
                   email: str, phone: str, program: str, year: int):
    from psycopg2.extras import RealDictCursor
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT student_id FROM student_profiles WHERE index_number=%s", (index_number,))
        row = cur.fetchone()
        if row:
            return row["student_id"]
    return insert_student_profile(conn, index_number, full_name, dob, gender, email, phone, program, year)

def add_grade_if_missing(conn, student_id: int, course_id: int, semester_id: int, score: float, academic_year: str):
    from psycopg2.extras import RealDictCursor
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT grade_id FROM grades WHERE student_id=%s AND course_id=%s AND semester_id=%s
        """, (student_id, course_id, semester_id))
        if cur.fetchone():
            return False
    letter = calculate_grade(score)
    gp = get_grade_point(score)
    return insert_grade(conn, student_id, course_id, semester_id, score, letter, gp, academic_year)

__all__ = [
    "generate_index", "generate_email", "generate_phone", "generate_birth_date", "pick_program",
    "select_courses", "generate_score", "ensure_course", "ensure_semester", "ensure_student", "add_grade_if_missing"
]
