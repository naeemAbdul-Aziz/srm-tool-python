# bulk_importer.py - handles bulk importing of student records from files

from db import (
    connect_to_db,
    insert_complete_student_record # This function handles profile and grade insertion transactionally
)
from file_handler import read_student_records, REQUIRED_FIELDS # Ensure REQUIRED_FIELDS is imported
from grade_util import calculate_grade
from logger import get_logger

logger = get_logger(__name__)

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
        
        for i, record in enumerate(valid_records, 1):
            try:
                # Prepare student_profile_data and grade_data from the record
                # Assuming 'index_number', 'name', 'dob', 'gender', 'program', 'year_of_study', 'contact_info' for profile
                # Assuming 'course_code', 'course_title', 'score', 'credit_hours', 'semester', 'academic_year' for grade
                
                # Basic validation for essential fields from the record
                if not all(k in record and record[k] for k in ['index_number', 'name', 'course_code', 'score', 'credit_hours', 'semester', 'academic_year']):
                    skipped += 1
                    error_msg = f"Skipping record {i} due to missing essential fields: {record}"
                    errors.append(error_msg)
                    logger.warning(error_msg)
                    continue

                student_profile_data = {
                    'index_number': record['index_number'],
                    'name': record['name'],
                    'dob': record.get('dob'), # Optional
                    'gender': record.get('gender'), # Optional
                    'program': record.get('program'), # Optional
                    'year_of_study': record.get('year_of_study'), # Optional
                    'contact_info': record.get('contact_info') # Optional
                }

                # Ensure score and credit_hours are integers/floats
                try:
                    score = float(record['score'])
                    credit_hours = int(record['credit_hours'])
                except ValueError as ve:
                    raise ValueError(f"Invalid numeric data for score or credit_hours: {ve}")

                grade_data = {
                    'course_code': record['course_code'],
                    'course_title': record['course_title'],
                    'score': score,
                    'credit_hours': credit_hours,
                    'semester': record['semester'], # This will be the semester_name
                    'academic_year': record.get('academic_year') # Optional
                }
                
                # Call the transactional function to insert profile and grade
                if insert_complete_student_record(conn, student_profile_data, grade_data):
                    successful += 1
                    logger.debug(f"successfully imported record {i}/{len(valid_records)}: {record['index_number']}")
                else:
                    skipped += 1
                    logger.warning(f"skipped record {i}/{len(valid_records)} for {record['index_number']} - database insertion failed")
                    
            except ValueError as e:
                skipped += 1
                error_msg = f"data conversion error for record {i} ({record.get('index_number', 'N/A')}): {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
            except Exception as e:
                skipped += 1
                error_msg = f"unexpected error processing record {i} ({record.get('index_number', 'N/A')}): {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
                
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