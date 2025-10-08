# file_handler.py - handles file reading and validation for student records

import os
import csv
try:
    from .logger import get_logger
    from .grade_util import calculate_grade  # Still used for internal logic if needed
except ImportError:
    from logger import get_logger
    from grade_util import calculate_grade

logger = get_logger(__name__)

# required fields for student record import
# These fields should match the columns expected in the CSV/TXT import file.
# 'dob' and 'gender' are added here as they are part of student_profiles now.
REQUIRED_FIELDS = [
    "index_number", "name", "dob", "gender", # Added dob and gender as they are in student_profiles
    "program", "year_of_study", "contact_info", # These are currently not in db.student_profiles, but kept for file parsing
    "course_code", "course_title", "score", "credit_hours", "semester", "academic_year"
]

def validate_record_fields(record: dict) -> tuple:
    """validate individual record fields and return validation status and errors"""
    errors = []
    
    try:
        # check for missing or empty required fields
        # Using a copy of REQUIRED_FIELDS to potentially exclude optional ones if needed in future
        current_required_fields = [f for f in REQUIRED_FIELDS if f not in ["program", "year_of_study", "contact_info"]] # These are optional for db insertion
        for field in current_required_fields:
            if field not in record or not str(record[field]).strip():
                errors.append(f"Missing or empty required field: '{field}'")

        # Validate index_number format (example: non-empty, alphanumeric)
        if 'index_number' in record and not record['index_number'].strip():
            errors.append("Index Number cannot be empty.")
        # Add more specific validation rules as needed (e.g., regex for index_number)

        # Validate score: must be a number between 0 and 100
        if 'score' in record and str(record['score']).strip():
            try:
                score = float(record['score'])
                if not (0 <= score <= 100):
                    errors.append("Score must be between 0 and 100.")
            except ValueError:
                errors.append("Score must be a valid number.")
        else:
            errors.append("Missing or empty required field: 'score'")
            
        # Validate credit_hours: must be a positive integer
        if 'credit_hours' in record and str(record['credit_hours']).strip():
            try:
                credit_hours = int(record['credit_hours'])
                if credit_hours <= 0:
                    errors.append("Credit Hours must be a positive integer.")
            except ValueError:
                errors.append("Credit Hours must be a valid integer.")
        else:
            errors.append("Missing or empty required field: 'credit_hours'")

        # Validate DOB format (YYYY-MM-DD)
        if 'dob' in record and record['dob'].strip():
            try:
                # Attempt to parse date, but don't store it here, just validate format
                from datetime import datetime
                datetime.strptime(record['dob'], '%Y-%m-%d')
            except ValueError:
                errors.append("Date of Birth (DOB) must be in YYYY-MM-DD format.")

    except Exception as e:
        errors.append(f"An unexpected error occurred during record validation: {str(e)}")
        logger.error(f"Error validating record {record.get('index_number', 'N/A')}: {e}")

    return not bool(errors), errors # True if valid, False otherwise, and list of errors

def read_student_records(file_path: str) -> tuple:
    """
    Reads student records from a CSV or TXT file, validates them,
    and returns a list of valid records and a list of errors.
    """
    logger.info(f"attempting to read and validate records from: {file_path}")
    valid_records = []
    errors = []
    
    file_extension = os.path.splitext(file_path)[1].lower()
    if file_extension not in ['.csv', '.txt']:
        errors.append(f"unsupported file type: {file_extension}. please provide a .csv or .txt file.")
        logger.error(f"unsupported file type: {file_extension} for {file_path}")
        return [], errors

    try:
        with open(file_path, mode='r', newline='', encoding='utf-8') as file:
            if file_extension == '.csv':
                reader = csv.DictReader(file)
            else: # Assume tab-separated for .txt
                reader = csv.DictReader(file, delimiter='\t')
            
            # Check if all REQUIRED_FIELDS are in the header
            fieldnames = reader.fieldnames or []
            missing_fields = [field for field in REQUIRED_FIELDS if field not in fieldnames]
            if missing_fields:
                errors.append(f"file is missing required headers: {', '.join(missing_fields)}")
                logger.error(f"file {file_path} missing headers: {missing_fields}")
                return [], errors

            total_rows = 0
            for i, row in enumerate(reader, 1):
                total_rows += 1
                record = {k.strip().lower().replace(' ', '_'): v.strip() for k, v in row.items()} # Clean keys and values
                
                is_valid, validation_errors = validate_record_fields(record)
                if is_valid:
                    valid_records.append(record)
                    logger.debug(f"successfully validated record on line {i}: {record.get('index_number', 'N/A')}")
                else:
                    if not validation_errors: # Fallback if no specific errors were captured by validate_record_fields
                        errors.append(f"invalid record on line {i} ({record.get('index_number', 'N/A')}) - unspecified error")
                    else:
                        error_msg = f"line {i} ({record.get('index_number', 'N/A')}): " + "; ".join(validation_errors)
                        errors.append(error_msg)
                        logger.warning(f"invalid record on line {i}: {validation_errors}")
                        
            logger.info(f"processed {total_rows} rows, {len(valid_records)} valid records found")

    except FileNotFoundError:
        error_msg = f"file not found: {file_path}"
        errors.append(error_msg)
        logger.error(error_msg)
    except PermissionError:
        error_msg = f"permission denied accessing file: {file_path}"
        errors.append(error_msg)
        logger.error(error_msg)
    except UnicodeDecodeError as e:
        error_msg = f"file encoding error: {str(e)}. try saving file as utf-8."
        errors.append(error_msg)
        logger.error(error_msg)
    except Exception as e:
        error_msg = f"unexpected error reading file: {str(e)}"
        errors.append(error_msg)
        logger.error(f"unexpected error reading file {file_path}: {e}")

    return valid_records, errors