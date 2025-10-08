#!/usr/bin/env python3
"""Comprehensive University of Ghana database seeding (refactored).

This module now delegates static data & generation helpers to:
 - seed_constants.py (names, schools, courses, calendar)
 - seed_helpers.py   (ensure_* + generation utilities)

Goal: reduce duplication & make incremental maintenance simpler.

Public entrypoint kept: seed_comprehensive_database(num_students=100, cleanup_first=True)
so existing API endpoints remain compatible.
"""

import os
import random
import sys
import argparse
from datetime import date
try:
    from .db import (
        connect_to_db, create_tables_if_not_exist, fetch_semester_by_name,
        fetch_course_by_code, fetch_student_by_index_number, ensure_assessment, insert_notification, _expand_audience_user_ids, create_user_notification_links
    )
    from .auth import create_user
    from .logger import get_logger
    from .seed_constants import (
        GHANAIAN_MALE_NAMES, GHANAIAN_FEMALE_NAMES, GHANAIAN_SURNAMES,
        UG_SCHOOLS_AND_PROGRAMS, UG_COMPREHENSIVE_COURSES, UG_ACADEMIC_CALENDAR
    )
    from .seed_helpers import (
        generate_index, generate_email, generate_phone, generate_birth_date,
        pick_program, select_courses, generate_score,
        ensure_course, ensure_semester, ensure_student, add_grade_if_missing
    )
except ImportError:
    from db import (
        connect_to_db, create_tables_if_not_exist, fetch_semester_by_name,
        fetch_course_by_code, fetch_student_by_index_number, ensure_assessment, insert_notification, _expand_audience_user_ids, create_user_notification_links
    )
    from auth import create_user
    from logger import get_logger
    from seed_constants import (
        GHANAIAN_MALE_NAMES, GHANAIAN_FEMALE_NAMES, GHANAIAN_SURNAMES,
        UG_SCHOOLS_AND_PROGRAMS, UG_COMPREHENSIVE_COURSES, UG_ACADEMIC_CALENDAR
    )
    from seed_helpers import (
        generate_index, generate_email, generate_phone, generate_birth_date,
        pick_program, select_courses, generate_score,
        ensure_course, ensure_semester, ensure_student, add_grade_if_missing
    )
from psycopg2.extras import RealDictCursor

logger = get_logger(__name__)

# ========================================
# (Constants moved to seed_constants)

# ========================================
# HELPER FUNCTIONS
# ========================================

# (Helpers moved to seed_helpers)

# ========================================
# MAIN SEEDING FUNCTIONS
# ========================================

def seed_comprehensive_courses(conn):
    """Seed all University of Ghana courses (idempotent)."""
    logger.info("COURSES: Seeding comprehensive UG course catalog...")
    success = 0
    for code, title, credits in UG_COMPREHENSIVE_COURSES:
        try:
            if ensure_course(conn, code, title, credits):
                success += 1
        except Exception as e:
            logger.debug(f"Course {code} exists or failed: {e}")
    logger.info(f"SUCCESS: Ensured {success}/{len(UG_COMPREHENSIVE_COURSES)} courses")
    return success

def seed_academic_calendar(conn):
    logger.info("CALENDAR: Seeding UG academic calendar...")
    ids = {}
    for name, year, start, end in UG_ACADEMIC_CALENDAR:
        try:
            sem_id = ensure_semester(conn, name, start, end, year)
            if sem_id:
                ids[name] = sem_id
        except Exception as e:
            logger.debug(f"Semester {name} exists or failed: {e}")
    logger.info(f"SUCCESS: Ensured {len(ids)}/{len(UG_ACADEMIC_CALENDAR)} semesters")
    return ids

def seed_diverse_students(conn, num_students=100):
    logger.info(f"STUDENTS: Seeding {num_students} diverse UG students...")
    distribution = [
        ("College of Basic and Applied Sciences", 0.25),
        ("College of Health Sciences", 0.15),
        ("College of Humanities", 0.15),
        ("College of Education", 0.10),
        ("Legon Business School", 0.20),
        ("School of Law", 0.05),
        ("School of Social Sciences", 0.10)
    ]
    student_ids = {}
    counter = 1
    for school, prop in distribution:
        target = int(num_students * prop)
        for _ in range(target):
            gender = random.choice(["Male", "Female"])
            first = random.choice(GHANAIAN_MALE_NAMES if gender == "Male" else GHANAIAN_FEMALE_NAMES)
            last = random.choice(GHANAIAN_SURNAMES)
            full_name = f"{first} {last}"
            year = random.randint(1,4)
            program = pick_program(school)
            index = generate_index(10000 + counter)
            counter += 1
            birth = generate_birth_date(year)
            email = generate_email(first, last, index)
            phone = generate_phone()
            ability = random.choices(["weak","average","strong","excellent"], weights=[15,50,25,10])[0]
            sid = ensure_student(conn, index, full_name, birth, gender, email, phone, program, year)
            if sid:
                student_ids[index] = {"student_id": sid, "data": {
                    "index_number": index, "full_name": full_name, "first_name": first,
                    "birth_date": birth, "gender": gender, "email": email, "phone": phone,
                    "program": program, "school": school, "year_of_study": year, "ability": ability
                }}
                # Ensure user account
                try:
                    password = index[-4:] + "2024"
                    create_user(index, password, 'student')
                except Exception as e:
                    logger.debug(f"User create skip {index}: {e}")
    logger.info(f"SUCCESS: Ensured {len(student_ids)} students")
    return student_ids

def seed_comprehensive_grades(conn, student_ids, semester_ids):
    logger.info("GRADES: Seeding comprehensive grade records...")
    count = 0
    for index, info in student_ids.items():
        sid = info["student_id"]
        data = info["data"]
        yos = data["year_of_study"]
        ability = data["ability"]
        # Derive semesters to grade (simplified mapping like original)
        mapping = [
            (1, ["1st Semester 2021/2022", "2nd Semester 2021/2022"]),
            (2, ["1st Semester 2022/2023", "2nd Semester 2022/2023"]),
            (3, ["1st Semester 2023/2024", "2nd Semester 2023/2024"]),
            (4, ["1st Semester 2024/2025"])
        ]
        semesters = []
        for level, sems in mapping:
            if yos >= level:
                semesters.extend(sems)
        if "2nd Semester 2024/2025" not in semesters:
            semesters.append("2nd Semester 2024/2025")
        for sem_name in semesters:
            sem_id = semester_ids.get(sem_name)
            if not sem_id:
                continue
            # approximate year level for earlier academic years
            if "2021/2022" in sem_name:
                sem_level = max(1, yos - 3)
            elif "2022/2023" in sem_name:
                sem_level = max(1, yos - 2)
            elif "2023/2024" in sem_name:
                sem_level = max(1, yos - 1)
            else:
                sem_level = yos
            courses = select_courses(data["program"], sem_level)
            academic_year = sem_name.split()[-1]
            for code, title, credits in courses:
                try:
                    with conn.cursor() as cur:
                        cur.execute("SELECT course_id FROM courses WHERE course_code=%s", (code,))
                        row = cur.fetchone()
                    if not row:
                        continue
                    course_id = row[0]
                    score = generate_score(sem_level, code, ability)
                    if add_grade_if_missing(conn, sid, course_id, sem_id, score, academic_year):
                        count += 1
                except Exception as e:
                    logger.debug(f"Skip grade {index} {code}: {e}")
    logger.info(f"SUCCESS: Ensured {count} grade records (may include pre-existing)")
    return count

def create_admin_accounts(conn):
    """Ensure core admin account (idempotent) and optionally extra demo admins.

    By default we now ONLY guarantee the primary 'admin' user to keep the
    role model simple (roles: admin | student). Additional legacy demo
    accounts ('registrar', 'dean') can be seeded by setting the environment
    variable SEED_EXTRA_ADMINS=true.
    """
    logger.info("ADMIN: Ensuring primary admin account...")

    primary_admin = ("admin", "admin123", "admin")
    extra_flag = os.getenv("SEED_EXTRA_ADMINS", "false").lower() in {"1","true","yes","on"}
    extra_accounts = []
    if extra_flag:
        extra_accounts = [
            ("registrar", "registrar123", "admin"),
            ("dean", "dean123", "admin")
        ]
        logger.info("SEED_EXTRA_ADMINS enabled: will ensure registrar and dean demo accounts")

    accounts = [primary_admin] + extra_accounts
    success_count = 0
    for username, password, role in accounts:
        try:
            created = create_user(username, password, role)
            if created:
                success_count += 1
                logger.info(f"Created admin account: {username}")
            else:
                logger.debug(f"Admin account already exists: {username}")
        except Exception as e:
            logger.warning(f"Admin account {username} creation error (may already exist): {e}")

    logger.info(f"SUCCESS: Ensured {success_count}/{len(accounts)} new admin account inserts (existing skipped)")
    return success_count

# ========================================
# DATABASE CLEANUP FUNCTIONS
# ========================================

def cleanup_existing_data(conn, full_reset=False):
    """Clean up existing data to avoid conflicts.

    Parameters:
        full_reset (bool): When True also deletes notifications, user_notifications, and admin users.
    """
    logger.info("CLEANUP: Removing existing data to avoid conflicts..." + (" (FULL RESET)" if full_reset else ""))
    try:
        with conn.cursor() as cursor:
            # Delete in reverse dependency order
            cursor.execute("DELETE FROM grades;")
            cursor.execute("DELETE FROM assessments;")
            if full_reset:
                cursor.execute("DELETE FROM user_notifications;")
                cursor.execute("DELETE FROM notifications;")
            cursor.execute("DELETE FROM student_profiles;")
            cursor.execute("DELETE FROM semesters;")
            cursor.execute("DELETE FROM courses;")
            # Remove student accounts always; optionally admins for full reset
            cursor.execute("DELETE FROM users WHERE role = 'student';")
            if full_reset:
                cursor.execute("DELETE FROM users WHERE role = 'admin';")
            conn.commit()
            logger.info("SUCCESS: Existing data cleaned up" + (" with full reset" if full_reset else ""))
            return True
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        conn.rollback()
        return False

# ========================================
# EXHAUSTIVE MODE HELPERS
# ========================================

def seed_assessments(conn, limit=None):
    """Seed three standard assessments per course (Quiz 20, Midterm 30, Final 50)."""
    logger.info("ASSESSMENTS: Seeding assessments...")
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT course_id, course_code FROM courses ORDER BY course_code")
            rows = cur.fetchall()
        if limit:
            rows = rows[:limit]
        count = 0
        for r in rows:
            cid = r['course_id']
            for name, max_score, weight in [
                ("Quiz", 20, 20.00), ("Midterm", 30, 30.00), ("Final Exam", 100, 50.00)
            ]:
                if ensure_assessment(conn, cid, name, max_score, weight):
                    count += 1
        logger.info(f"SUCCESS: Ensured {count} assessments")
        return count
    except Exception as e:
        logger.error(f"Error seeding assessments: {e}")
        return 0

def ensure_current_semester(conn, semester_name="2nd Semester 2024/2025"):
    from db import set_current_semester, fetch_semester_by_name
    sem = fetch_semester_by_name(conn, semester_name)
    if not sem:
        logger.warning(f"Cannot set current semester: {semester_name} not found")
        return False
    return set_current_semester(conn, sem['semester_id'])

def enforce_program_coverage(conn):
    """Ensure at least one student exists for every program across schools."""
    logger.info("PROGRAM COVERAGE: Ensuring one student per program...")
    added = 0
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT program FROM student_profiles")
        existing = {r['program'] for r in cur.fetchall() if r['program']}
    for school, programs in UG_SCHOOLS_AND_PROGRAMS.items():
        for program in programs:
            if program not in existing:
                # deterministic pseudo index
                base = abs(hash(program)) % 90000 + 10000
                index = generate_index(base)
                first = program.split()[0][:6] or 'Stud'
                last = 'Program'
                full_name = f"{first} {last}"
                birth = generate_birth_date(1)
                email = generate_email(first, last, index)
                phone = generate_phone()
                sid = ensure_student(conn, index, full_name, birth, 'Male', email, phone, program, 1)
                if sid:
                    try:
                        create_user(index, index[-4:]+"2024", 'student')
                    except Exception:
                        pass
                    added += 1
    logger.info(f"PROGRAM COVERAGE: Added {added} synthetic students for missing programs")
    return added

def create_partial_students(conn, count=5):
    logger.info(f"PARTIAL: Creating {count} partial/no-grade students...")
    created = 0
    for i in range(count):
        index = generate_index(90000 + i)
        full_name = f"Partial Student {i+1}"
        birth = generate_birth_date(1)
        email = generate_email('partial', str(i+1), index)
        phone = generate_phone()
        if ensure_student(conn, index, full_name, birth, 'Female' if i % 2 else 'Male', email, phone, pick_program(random.choice(list(UG_SCHOOLS_AND_PROGRAMS.keys()))), 1):
            try:
                create_user(index, index[-4:]+"2024", 'student')
            except Exception:
                pass
            created += 1
    logger.info(f"PARTIAL: Created {created} partial students")
    return created

def curate_edge_case_students(conn):
    """Adjust a few students to have perfect, failing, and boundary scores (updates)."""
    logger.info("EDGE CASES: Curating GPA boundary students...")
    updated = 0
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT student_id, index_number FROM student_profiles ORDER BY index_number LIMIT 12")
            students = cur.fetchall()
        if not students:
            return 0
        boundary_scores = [49,50,59,60,69,70,79,80]
        from db import fetch_all_courses, fetch_all_semesters
        courses = fetch_all_courses(connect_to_db())
        semesters = fetch_all_semesters(connect_to_db())
        course_ids = [c['course_id'] for c in courses[:len(boundary_scores)]]
        sem_ids = [s['semester_id'] for s in semesters[:2]]  # use two semesters
        # Perfect student (first)
        if students:
            sid = students[0]['student_id']
            _set_scores_for_student(conn, sid, course_ids, sem_ids, 95)
            updated += 1
        # Failing student (second)
        if len(students) > 1:
            sid = students[1]['student_id']
            _set_scores_for_student(conn, sid, course_ids, sem_ids, 35)
            updated += 1
        # Boundary student (third)
        if len(students) > 2:
            sid = students[2]['student_id']
            _set_scores_for_student(conn, sid, course_ids[:len(boundary_scores)], sem_ids[:1], None, boundary_scores)
            updated += 1
        logger.info(f"EDGE CASES: Updated {updated} curated students")
        return updated
    except Exception as e:
        logger.error(f"EDGE CASES: Error curating boundary students: {e}")
        return updated

def _set_scores_for_student(conn, student_id, course_ids, semester_ids, uniform_score=None, score_list=None):
    from db import update_student_score
    with conn.cursor() as cur:
        # Map semesters if needed
        for sem_id in semester_ids:
            for idx, course_id in enumerate(course_ids):
                score = uniform_score if uniform_score is not None else (score_list[idx % len(score_list)] if score_list else 75)
                # Derive grade & grade_point using helpers
                from grade_util import calculate_grade, get_grade_point
                grade = calculate_grade(score)
                gp = get_grade_point(score)
                # Fetch academic year
                cur.execute("SELECT academic_year FROM semesters WHERE semester_id=%s", (sem_id,))
                ay = cur.fetchone()[0]
                update_student_score(conn, student_id, course_id, sem_id, score, grade, gp, ay)

def seed_sample_notifications(conn):
    if os.getenv("SUPPRESS_SEED_NOTIFICATIONS"):
        logger.info("NOTIFICATIONS: Suppressed; skipping sample notifications")
        return 0,0
    logger.info("NOTIFICATIONS: Seeding sample notifications...")
    created = 0
    linked = 0
    try:
        msgs = [
            ("system_welcome","Welcome","System initialization complete","info","all"),
            ("semester_upcoming","Upcoming Semester","Next semester begins soon","warning","students"),
            ("maintenance","Maintenance Window","Planned downtime this weekend","critical","all"),
            ("policy_update","Policy Update","Assessment policy updated","info","admins")
        ]
        for type_, title, msg, sev, audience in msgs:
            nid = insert_notification(conn, type_, title, msg, sev, audience)
            if nid:
                created += 1
                uids = _expand_audience_user_ids(conn, audience)
                linked += create_user_notification_links(conn, nid, uids)
        logger.info(f"NOTIFICATIONS: Created {created} notifications; linked {linked} user notifications")
        return created, linked
    except Exception as e:
        logger.error(f"NOTIFICATIONS: Error seeding notifications: {e}")
        return created, linked

def flip_some_notifications_read(conn, fraction=0.4):
    if os.getenv("SUPPRESS_SEED_NOTIFICATIONS"):
        return 0
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id FROM user_notifications ORDER BY id")
            rows = cur.fetchall()
        to_mark = rows[:int(len(rows)*fraction)]
        changed = 0
        from db import mark_notification_read
        for r in to_mark:
            # Need user_id; fetch
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT user_id FROM user_notifications WHERE id=%s", (r['id'],))
                res = cur.fetchone()
            if res:
                uid = res['user_id']
                if mark_notification_read(conn, uid, r['id']):
                    changed += 1
        logger.info(f"NOTIFICATIONS: Marked {changed} user notifications read")
        return changed
    except Exception as e:
        logger.error(f"NOTIFICATIONS: Error marking read: {e}")
        return 0

# ========================================
# MAIN EXECUTION FUNCTION
# ========================================

def seed_comprehensive_database(num_students=100, cleanup_first=True, random_seed=None, suppress_notifications=False,
                                baseline=False, exhaustive=False, assessments_sample=None, full_reset=False):
    """Main function to seed comprehensive University of Ghana database

    Parameters:
        num_students (int): Number of student profiles to create.
        cleanup_first (bool): Whether to wipe existing related data first.
        random_seed (Optional[Union[int,str]]): If provided (or if env var SEED_RANDOM_SEED set),
            the global random module will be seeded for deterministic reproducibility.
            This affects index generation, course selection ordering, ability assignment,
            scores, names, etc. Use this for stable test fixtures.
        suppress_notifications (bool): When True, sets an environment flag
            SUPPRESS_SEED_NOTIFICATIONS=1 that downstream logic (future notification
            emitters) can honor to avoid generating noisy bulk notifications during seeding.
            Currently no notifications are emitted by seeding, but this scaffolds future use.
    """
    try:
        print("UNIVERSITY OF GHANA COMPREHENSIVE DATABASE SEEDING")
        print("=" * 60)
        logger.info("Starting comprehensive database seeding...")

        # Resolve deterministic random seed (parameter overrides env var)
        env_seed = os.getenv("SEED_RANDOM_SEED")
        effective_seed = random_seed if random_seed is not None else env_seed
        if effective_seed is not None and effective_seed != "":
            # Coerce to int when possible for readability; else use raw string
            try:
                seed_val = int(str(effective_seed))
            except ValueError:
                seed_val = str(effective_seed)
            random.seed(seed_val)
            logger.info(f"Deterministic random seed set: {seed_val}")
            print(f"DETERMINISM: Using random seed = {seed_val}")
        else:
            logger.info("Random seed not specified; using nondeterministic run")

        # Handle suppression flag
        if suppress_notifications:
            os.environ["SUPPRESS_SEED_NOTIFICATIONS"] = "1"
            logger.info("Notifications suppressed for this seeding run (flag set)")
            print("NOTIFICATIONS: Suppression enabled (no bulk notifications will be emitted)")
        else:
            # Clear any stale flag from prior processes if present
            if os.environ.get("SUPPRESS_SEED_NOTIFICATIONS"):
                os.environ.pop("SUPPRESS_SEED_NOTIFICATIONS", None)
        
        # Connect to database
        conn = connect_to_db()
        if not conn:
            logger.error("Failed to connect to database")
            return False
        
        # Clean up existing data if requested
        if cleanup_first:
            print("CLEANUP: Removing existing data...")
            if not cleanup_existing_data(conn, full_reset=full_reset):
                logger.error("Failed to cleanup existing data")
                return False
            print("SUCCESS: Cleanup completed")
        
        # Create tables
        logger.info("TABLES: Creating database tables...")
        create_tables_if_not_exist(conn)
        print("SUCCESS: Database schema ready")
        
        # Determine mode description
        mode_label = 'BASELINE' if baseline else ('EXHAUSTIVE' if exhaustive else 'COMPREHENSIVE')
        print(f"MODE: {mode_label}")

        # Seed courses
        course_count = seed_comprehensive_courses(conn)
        print(f"SUCCESS: Courses seeded: {course_count}")
        
        # Seed academic calendar
        semester_ids = seed_academic_calendar(conn)
        print(f"SUCCESS: Semesters seeded: {len(semester_ids)}")
        
        # Create admin accounts
        admin_count = create_admin_accounts(conn)
        print(f"SUCCESS: Admin accounts created: {admin_count}")
        
        # Seed students (baseline fewer students override)
        target_students = num_students if not baseline else min(num_students, 10)
        student_ids = seed_diverse_students(conn, target_students)
        print(f"SUCCESS: Students seeded: {len(student_ids)}")
        
        grade_count = 0
        if not baseline:
            grade_count = seed_comprehensive_grades(conn, student_ids, semester_ids)
            print(f"SUCCESS: Grades seeded: {grade_count}")
        else:
            print("BASELINE: Skipping full grade expansion")

        # Exhaustive enhancements
        added_program_students = partial_students = curated = assessments_count = notif_created = notif_links = notif_marked = 0
        current_sem = False
        if exhaustive:
            added_program_students = enforce_program_coverage(conn)
            partial_students = create_partial_students(conn, count=5)
            curated = curate_edge_case_students(conn)
            assessments_count = seed_assessments(conn, limit=assessments_sample)
            current_sem = ensure_current_semester(conn)
            notif_created, notif_links = seed_sample_notifications(conn)
            notif_marked = flip_some_notifications_read(conn)
        elif assessments_sample:
            # allow sampling assessments in non-exhaustive mode
            assessments_count = seed_assessments(conn, limit=assessments_sample)
        
        conn.close()
        
        # Final summary
        print("\n" + "=" * 60)
        print(f"{mode_label} SEEDING COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"SUMMARY:")
        print(f"   Courses: {course_count}")
        print(f"   Semesters: {len(semester_ids)}")
        print(f"   Admin accounts: {admin_count}")
        print(f"   Students: {len(student_ids)}")
        print(f"   Grade records: {grade_count}")
        if exhaustive:
            print(f"   Added program coverage students: {added_program_students}")
            print(f"   Partial students: {partial_students}")
            print(f"   Curated edge-case students: {curated}")
            print(f"   Assessments: {assessments_count}")
            print(f"   Notifications created: {notif_created} (links: {notif_links}, marked read: {notif_marked})")
            print(f"   Current semester set: {current_sem}")
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
    description = (
        "Comprehensive University of Ghana dataset seeder. Generates courses, semesters, admin accounts, "
        "students, and grades. Supports deterministic runs and notification suppression."
    )
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--num-students", type=int, default=100, help="Number of students to seed (default 100)")
    parser.add_argument("--no-clean", action="store_true", help="Do NOT cleanup existing data first")
    parser.add_argument("--seed", dest="seed", help="Deterministic random seed (int or string)")
    parser.add_argument("--suppress-notifications", action="store_true", help="Suppress notifications during seeding (sets SUPPRESS_SEED_NOTIFICATIONS=1)")
    parser.add_argument("--yes", "-y", action="store_true", help="Auto-confirm without interactive prompts")
    parser.add_argument("--baseline", action="store_true", help="Seed minimal baseline dataset (overrides some counts)")
    parser.add_argument("--exhaustive", action="store_true", help="Seed exhaustive dataset (edge cases, assessments, notifications)")
    parser.add_argument("--assessments-sample", type=int, help="Limit number of courses for which assessments are generated")
    parser.add_argument("--full-reset", action="store_true", help="Full reset including notifications and admin users")

    # If no additional CLI args beyond script name, fall back to legacy interactive mode
    if len(sys.argv) == 1:
        print("University of Ghana Comprehensive Database Seeding")
        print("This will create a complete academic dataset with:")
        print("• 130+ courses across all UG schools")
        print("• 8 academic semesters (2021-2025)")
        print("• 100 diverse students with realistic profiles")
        print("• Comprehensive grade records")
        print("• Multiple admin accounts")
        print()
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
        seed_in = input("Optional deterministic random seed (blank for random): ").strip() or None
        suppress = input("Suppress notifications during seeding? (y/N): ").strip().lower() in ["y", "yes"]
        confirm = input(f"Proceed with seeding {num_students} students (seed={seed_in or 'auto'}, suppress_notifications={suppress})? (y/N): ")
        if confirm.lower() in ['y', 'yes']:
            success = seed_comprehensive_database(num_students, cleanup_first, random_seed=seed_in, suppress_notifications=suppress)
            if success:
                print("\nSUCCESS: Database seeding completed successfully!")
                print("You can now use the full system with comprehensive UG data.")
            else:
                print("\nERROR: Database seeding failed. Check logs for details.")
        else:
            print("Operation cancelled.")
        sys.exit(0)

    args = parser.parse_args()
    cleanup_first = not args.no_clean
    seed_val = args.seed
    suppress = args.suppress_notifications

    if not args.yes:
        prompt = f"Proceed with seeding {args.num_students} students (seed={seed_val or 'auto'}, suppress_notifications={suppress}, cleanup_first={cleanup_first})? (y/N): "
        if input(prompt).strip().lower() not in ['y', 'yes']:
            print("Operation cancelled.")
            sys.exit(0)

    # Validate mutually exclusive modes
    if args.baseline and args.exhaustive:
        print("ERROR: --baseline and --exhaustive cannot be used together.")
        sys.exit(1)

    success = seed_comprehensive_database(
        num_students=args.num_students,
        cleanup_first=cleanup_first,
        random_seed=seed_val,
        suppress_notifications=suppress,
        baseline=args.baseline,
        exhaustive=args.exhaustive,
        assessments_sample=args.assessments_sample,
        full_reset=args.full_reset
    )
    if success:
        print("\nSUCCESS: Database seeding completed successfully!")
        print("You can now use the full system with comprehensive UG data.")
    else:
        print("\nERROR: Database seeding failed. Check logs for details.")
