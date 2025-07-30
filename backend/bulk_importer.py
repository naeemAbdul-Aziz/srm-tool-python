# bulk_importer.py - handles bulk importing of student records from files

from db import (
    connect_to_db,
    insert_student_profile,
    insert_grade
)
from file_handler import read_student_records
from grade_util import calculate_grade
from logger import get_logger

logger = get_logger(__name__)

def bulk_import_from_file(file_path: str) -> dict:
    """import student profiles and grades from a structured csv/txt file"""
    logger.info(f"starting bulk import from file: {file_path}")
    
    # read and validate records from file
    valid_records, errors = read_student_records(file_path)

    if not valid_records:
        logger.warning(f"no valid records found in file: {file_path}")
        return {
            "message": "no valid records found.",
            "total": 0,
            "successful": 0,
            "skipped": 0,
            "errors": errors
        }

    # establish database connection
    conn = connect_to_db()
    if conn is None:
        logger.error("database connection failed during bulk import")
        return {
            "message": "database connection failed.",
            "total": len(valid_records),
            "successful": 0,
            "skipped": len(valid_records),
            "errors": ["could not connect to the database."]
        }

    successful = 0
    skipped = 0

    try:
        logger.info(f"processing {len(valid_records)} records for bulk import")
        
        for i, record in enumerate(valid_records, 1):
            try:
                # prepare student profile data
                profile = {
                    "index_number": record["index_number"],
                    "name": record["name"],
                    "program": record.get("program", ""),
                    "year_of_study": record.get("year_of_study", ""),
                    "contact_info": record.get("contact_info", "")
                }

                # prepare grade data
                grade = {
                    "index_number": record["index_number"],
                    "course_code": record["course_code"],
                    "course_title": record["course_title"],
                    "score": float(record["score"]),
                    "credit_hours": int(record["credit_hours"]),
                    "letter_grade": calculate_grade(float(record["score"])),
                    "semester": record["semester"],
                    "academic_year": record["academic_year"]
                }

                # attempt to insert both profile and grade
                if insert_student_profile(conn, profile) and insert_grade(conn, grade):
                    successful += 1
                    logger.debug(f"successfully imported record {i}/{len(valid_records)}: {record['index_number']}")
                else:
                    skipped += 1
                    logger.warning(f"skipped record {i}/{len(valid_records)} for {record['index_number']} - database insertion failed")
                    
            except ValueError as e:
                skipped += 1
                error_msg = f"data conversion error for record {i}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
            except Exception as e:
                skipped += 1
                error_msg = f"unexpected error processing record {i}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
                
        # commit all successful transactions
        conn.commit()
        logger.info(f"bulk import completed: {successful} successful, {skipped} skipped")
        
    except Exception as e:
        logger.error(f"bulk import failed with critical error: {e}")
        conn.rollback()
        errors.append(f"critical import error: {str(e)}")
    finally:
        conn.close()

    return {
        "message": "bulk import complete.",
        "total": len(valid_records),
        "successful": successful,
        "skipped": skipped,
        "errors": errors
    }
