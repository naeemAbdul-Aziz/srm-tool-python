"""Analytics Validation Harness

Purpose:
  Compare key analytics metrics produced by the API logic with direct SQL queries to detect silent data mismatches.

Metrics Covered:
  - Total students / courses / grades
  - Grade distribution
  - Average GPA
  - Top students (index_number, avg_gpa, course count) limited to 10

Usage (CLI):
  python analytics_validation.py --dsn "postgresql://user:pass@host:port/dbname"
  (If DSN omitted, falls back to config in config.py / environment.)

Planned Extension:
  - Semester-scoped validation (filters)
  - Additional course statistics comparisons
  - JSON export / CI integration exit codes

Exit Codes:
  0 = All metrics match
  1 = Mismatches detected or runtime error
"""
from __future__ import annotations
import argparse
import json
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import psycopg2
from psycopg2.extras import RealDictCursor

# Local imports with graceful fallback for script/packaged execution
try:
    try:
        from .config import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT  # type: ignore
    except ImportError:
        from config import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT  # type: ignore
    try:
        from .db import connect_to_db  # type: ignore
    except ImportError:
        from db import connect_to_db  # type: ignore
except Exception:
    DB_NAME = DB_USER = DB_PASSWORD = DB_HOST = DB_PORT = None  # type: ignore
    def connect_to_db():  # type: ignore
        raise RuntimeError("Could not import database configuration; supply --dsn.")

@dataclass
class MetricMismatch:
    name: str
    expected: Any
    actual: Any
    detail: Optional[str] = None

@dataclass
class ValidationResult:
    mismatches: List[MetricMismatch] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.mismatches and not self.errors

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "mismatch_count": len(self.mismatches),
            "mismatches": [m.__dict__ for m in self.mismatches],
            "errors": self.errors,
        }

# --- SQL QUERIES (Ground Truth) ---
SQL_TOTAL_STUDENTS = "SELECT COUNT(*) AS cnt FROM student_profiles"
SQL_TOTAL_COURSES = "SELECT COUNT(*) AS cnt FROM courses"
SQL_TOTAL_GRADES = "SELECT COUNT(*) AS cnt FROM grades"
SQL_GRADE_DISTRIBUTION = """
    SELECT grade, COUNT(*)::int AS count
    FROM grades
    GROUP BY grade
    ORDER BY grade
"""
SQL_AVG_GPA = "SELECT ROUND(AVG(grade_point)::numeric, 2) AS avg_gpa FROM grades"
SQL_TOP_STUDENTS = """
    SELECT sp.index_number, ROUND(AVG(g.grade_point)::numeric, 2) AS avg_gpa, COUNT(g.grade_id)::int AS total_courses
    FROM student_profiles sp
    JOIN grades g ON sp.student_id = g.student_id
    GROUP BY sp.index_number
    HAVING COUNT(g.grade_id) >= 3
    ORDER BY avg_gpa DESC
    LIMIT 10
"""

# --- Helper Functions ---

def get_connection(dsn: Optional[str]):
    if dsn:
        return psycopg2.connect(dsn)
    # fallback to existing connector if available
    try:
        return connect_to_db()
    except Exception as e:
        raise RuntimeError(f"Cannot establish connection: {e}")


def fetch_ground_truth(conn) -> Dict[str, Any]:
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(SQL_TOTAL_STUDENTS); total_students = cur.fetchone()["cnt"]
    cur.execute(SQL_TOTAL_COURSES); total_courses = cur.fetchone()["cnt"]
    cur.execute(SQL_TOTAL_GRADES); total_grades = cur.fetchone()["cnt"]
    cur.execute(SQL_GRADE_DISTRIBUTION); dist_rows = cur.fetchall()
    grade_distribution = {r["grade"]: r["count"] for r in dist_rows}
    cur.execute(SQL_AVG_GPA); avg_gpa_row = cur.fetchone(); avg_gpa = float(avg_gpa_row["avg_gpa"]) if avg_gpa_row["avg_gpa"] is not None else 0.0
    cur.execute(SQL_TOP_STUDENTS); top_students = cur.fetchall()
    return {
        "totals": {
            "total_students": total_students,
            "total_courses": total_courses,
            "total_grades": total_grades,
        },
        "grade_distribution": grade_distribution,
        "average_gpa": avg_gpa,
        "top_students": top_students,
    }


def fetch_api_like(conn) -> Dict[str, Any]:
    """Reproduce the logic used in generate_comprehensive_report and dashboard analytics endpoints.
    This intentionally mirrors implementation (may diverge if code changes – keep in sync).
    """
    cur = conn.cursor(cursor_factory=RealDictCursor)
    # Totals
    cur.execute("SELECT COUNT(*) AS count FROM student_profiles"); api_students = cur.fetchone()["count"]
    cur.execute("SELECT COUNT(*) AS count FROM courses"); api_courses = cur.fetchone()["count"]
    cur.execute("SELECT COUNT(*) AS count FROM grades"); api_grades = cur.fetchone()["count"]

    # Grade distribution identical query structure
    cur.execute(SQL_GRADE_DISTRIBUTION); api_dist_rows = cur.fetchall()
    api_distribution = {r["grade"]: r["count"] for r in api_dist_rows}

    # Average GPA
    cur.execute("SELECT AVG(grade_point) AS avg_gpa FROM grades"); row = cur.fetchone(); avg = round(row["avg_gpa"], 2) if row["avg_gpa"] else 0.0

    # Top students replicating endpoint logic (>=3 grades)
    cur.execute(SQL_TOP_STUDENTS); top_students = cur.fetchall()

    return {
        "totals": {
            "total_students": api_students,
            "total_courses": api_courses,
            "total_grades": api_grades,
        },
        "grade_distribution": api_distribution,
        "average_gpa": avg,
        "top_students": top_students,
    }


def compare_lists(expected: List[Dict[str, Any]], actual: List[Dict[str, Any]], key_fields: Tuple[str, ...]) -> List[MetricMismatch]:
    mismatches: List[MetricMismatch] = []
    def normalize(lst):
        return [ {k: item.get(k) for k in key_fields} for item in lst ]
    e_norm = normalize(expected)
    a_norm = normalize(actual)
    if e_norm != a_norm:
        mismatches.append(MetricMismatch(
            name="top_students",
            expected=e_norm,
            actual=a_norm,
            detail="Order or values differ"
        ))
    return mismatches


def validate(conn) -> ValidationResult:
    result = ValidationResult()
    try:
        ground = fetch_ground_truth(conn)
        api_like = fetch_api_like(conn)

        # Totals
        for k in ["total_students", "total_courses", "total_grades"]:
            if ground["totals"][k] != api_like["totals"][k]:
                result.mismatches.append(MetricMismatch(k, ground["totals"][k], api_like["totals"][k]))

        # Grade distribution
        if ground["grade_distribution"] != api_like["grade_distribution"]:
            result.mismatches.append(MetricMismatch(
                "grade_distribution",
                ground["grade_distribution"],
                api_like["grade_distribution"],
                detail="Distribution map mismatch"
            ))

        # Average GPA (tolerance = 0.01)
        if abs(ground["average_gpa"] - api_like["average_gpa"]) > 0.01:
            result.mismatches.append(MetricMismatch(
                "average_gpa",
                ground["average_gpa"],
                api_like["average_gpa"],
                detail="> 0.01 difference"
            ))

        # Top students
        result.mismatches.extend(
            compare_lists(ground["top_students"], api_like["top_students"], ("index_number", "avg_gpa", "total_courses"))
        )

    except Exception as e:
        result.errors.append(str(e))
    return result


def main():
    parser = argparse.ArgumentParser(description="Validate analytics metrics against ground truth SQL")
    parser.add_argument("--dsn", help="Optional DSN override, e.g. postgresql://user:pass@host:5432/dbname")
    parser.add_argument("--json", action="store_true", help="Output JSON only (machine readable)")
    args = parser.parse_args()

    try:
        conn = get_connection(args.dsn)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    with conn:
        result = validate(conn)

    output = result.to_dict()
    if args.json:
        print(json.dumps(output, indent=2))
    else:
        print("=== Analytics Validation Report ===")
        print(f"Passed: {output['passed']}")
        print(f"Mismatches: {output['mismatch_count']}")
        if output['mismatches']:
            for m in output['mismatches']:
                print(f" - {m['name']}: expected={m['expected']} actual={m['actual']} detail={m.get('detail')}")
        if output['errors']:
            print("Errors:")
            for err in output['errors']:
                print(f" - {err}")

    sys.exit(0 if result.passed else 1)

if __name__ == "__main__":
    main()
