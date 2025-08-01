# bulk_importer.py - handles bulk importing of student records from files

from db import (
    connect_to_db,
    insert_complete_student_record # This function handles profile and grade insertion transactionally
)
from file_handler import read_student_records, REQUIRED_FIELDS # Ensure REQUIRED_FIELDS is imported
from grade_util import calculate_grade
from logger import get_logger

logger = get_logger(__name__)

# Update REQUIRED_FIELDS to match the new schema
REQUIRED_FIELDS = [
    'index_number', 'name', 'dob', 'gender', 'program', 'year_of_study', 'contact_info',
    'course_code', 'score', 'credit_hours', 'semester', 'academic_year'
]

# Modularized validation logic
def validate_index_number(index_number):
    """Validate the format of index_number."""
    if not index_number.startswith('ug') or len(index_number) != 7:
        return False, f"Invalid index_number format: {index_number}"
    return True, None

# The bulk_import_from_file function signature now accepts semester_name
def bulk_import_from_file(file_path: str, required_fields: list, semester_name: str) -> dict:
    """import student profiles and grades from a structured csv/txt file."""
    logger.info(f"starting bulk import from file: {file_path} for semester: {semester_name}")
    
    # Read and validate records from file using the new REQUIRED_FIELDS from file_handler
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

    successful = 0
    skipped = 0

    try:
        conn = connect_to_db()
        if not conn:
            logger.error("Failed to connect to database for bulk import.")
            errors.append("Database connection failed.")
            return {
                "message": "bulk import failed due to database connection error.",
                "total": len(valid_records),
                "successful": 0,
                "skipped": len(valid_records),
                "errors": errors
            }

        logger.info(f"processing {len(valid_records)} records for bulk import")
        
        # Ensure index_number format and password generation
        for record in valid_records:
            is_valid, error_msg = validate_index_number(record['index_number'])
            if not is_valid:
                errors.append(error_msg)
                logger.warning(error_msg)
                skipped += 1
                continue

            try:
                # Insert student profile and grades
                student_profile_data = {
                    "index_number": record['index_number'],
                    "full_name": record['name'],
                    "dob": record['dob'],
                    "gender": record['gender'],
                    "contact_email": record['contact_info'],
                    "contact_phone": None,
                    "program": record['program'],
                    "year_of_study": record['year_of_study']
                }

                grade_data = [{
                    "course_code": record['course_code'],
                    "score": record['score'],
                    "semester": semester_name,
                    "academic_year": record['academic_year']
                }]

                insert_complete_student_record(conn, student_profile_data, grade_data)
                logger.info(f"Successfully imported record for index_number: {record['index_number']}")
                successful += 1
            except Exception as e:
                error_msg = f"Error importing record for index_number {record['index_number']}: {e}"
                errors.append(error_msg)
                logger.error(error_msg)
                skipped += 1

        logger.info(f"bulk import completed: {successful} successful, {skipped} skipped")
        
    except Exception as e:
        logger.error(f"bulk import failed with critical error: {e}")
        errors.append(f"critical import error: {str(e)}")
    finally:
        if conn:
            conn.close() # Ensure the connection is closed after all operations

    return {
        "message": "bulk import complete.",
        "total": len(valid_records),
        "successful": successful,
        "skipped": skipped,
        "errors": errors
    }