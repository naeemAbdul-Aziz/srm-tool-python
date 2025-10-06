import os
import pytest
from comprehensive_seed import seed_comprehensive_database
from db import connect_to_db

@pytest.mark.seeding
def test_deterministic_seed_produces_stable_counts(monkeypatch):
    """Run seeding twice with same seed and assert stable entity counts."""
    seed = 123
    # First run
    assert seed_comprehensive_database(num_students=25, cleanup_first=True, random_seed=seed, suppress_notifications=True)
    conn1 = connect_to_db(); assert conn1
    with conn1.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM courses"); courses_1 = (cur.fetchone() or (0,))[0]
        cur.execute("SELECT COUNT(*) FROM semesters"); semesters_1 = (cur.fetchone() or (0,))[0]
        cur.execute("SELECT COUNT(*) FROM student_profiles"); students_1 = (cur.fetchone() or (0,))[0]
        cur.execute("SELECT COUNT(*) FROM grades"); grades_1 = (cur.fetchone() or (0,))[0]
        cur.execute("SELECT COUNT(*) FROM notifications"); notifications_1 = (cur.fetchone() or (0,))[0]
    conn1.close()

    # Second run (cleanup to ensure identical regeneration)
    assert seed_comprehensive_database(num_students=25, cleanup_first=True, random_seed=seed, suppress_notifications=True)
    conn2 = connect_to_db(); assert conn2
    with conn2.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM courses"); courses_2 = (cur.fetchone() or (0,))[0]
        cur.execute("SELECT COUNT(*) FROM semesters"); semesters_2 = (cur.fetchone() or (0,))[0]
        cur.execute("SELECT COUNT(*) FROM student_profiles"); students_2 = (cur.fetchone() or (0,))[0]
        cur.execute("SELECT COUNT(*) FROM grades"); grades_2 = (cur.fetchone() or (0,))[0]
        cur.execute("SELECT COUNT(*) FROM notifications"); notifications_2 = (cur.fetchone() or (0,))[0]
    conn2.close()

    assert (courses_1, semesters_1, students_1, grades_1) == (courses_2, semesters_2, students_2, grades_2)
    # Suppression should prevent notification creation
    assert notifications_1 == 0 and notifications_2 == 0

@pytest.mark.seeding
def test_env_seed(monkeypatch):
    """Ensure environment variable seed works when param omitted."""
    monkeypatch.setenv('SEED_RANDOM_SEED', '555')
    assert seed_comprehensive_database(num_students=5, cleanup_first=True, random_seed=None, suppress_notifications=True)
    # Quick sanity: counts > 0
    conn = connect_to_db(); assert conn
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM student_profiles"); students = (cur.fetchone() or (0,))[0]
    conn.close()
    assert students == 5
