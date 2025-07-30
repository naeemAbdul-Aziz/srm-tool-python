# bulk_importer.py

from db import connect_to_db, insert_student_record
from file_handler import read_student_records
from grade_util import calculate_grade
from logger import get_logger

logger = get_logger(__name__)

def bulk_import_from_file(file_path: str) -> dict:
    """
    Imports student records from a file (.csv or .txt).
    Returns a summary dictionary: total, successful, skipped, and errors.
    """
    valid_records, errors = read_student_records(file_path)

    if not valid_records:
        return {
            "message": "No valid records found.",
            "total": 0,
            "successful": 0,
            "skipped": 0,
            "errors": errors
        }

    conn = connect_to_db()
    if conn is None:
        return {
            "message": "Database connection failed.",
            "total": len(valid_records),
            "successful": 0,
            "skipped": len(valid_records),
            "errors": ["Could not connect to the database."]
        }

    successful_imports = 0
    try:
        for record in valid_records:
            record["grade"] = calculate_grade(record["score"])
            if insert_student_record(conn, record):
                successful_imports += 1
            else:
                logger.warning(f"Skipped record {record['index_number']}")
        conn.commit()
    except Exception as e:
        logger.error(f"Bulk import failed: {e}")
        conn.rollback()
        errors.append(str(e))
    finally:
        conn.close()

    return {
        "message": "Bulk import complete.",
        "total": len(valid_records),
        "successful": successful_imports,
        "skipped": len(valid_records) - successful_imports,
        "errors": errors
    }
