# file_handler.py - handles file reading and validation for student records

import os
import csv
from logger import get_logger
from grade_util import calculate_grade

logger = get_logger(__name__)

# required fields for student record import
REQUIRED_FIELDS = [
    "index_number", "name", "program", "year_of_study", "contact_info",
    "course_code", "course_title", "score", "credit_hours", "semester", "academic_year"
]

def validate_record_fields(record: dict) -> tuple:
    """validate individual record fields and return validation status and errors"""
    errors = []
    
    try:
        # check for missing or empty required fields
        for field in REQUIRED_FIELDS:
            if field not in record or not str(record[field]).strip():
                errors.append(f"missing or empty field: {field}")

        # validate index number format
        if record.get("index_number"):
            index_str = str(record["index_number"]).strip()
            if not index_str.isdigit():
                errors.append("index number must be numeric")
        
        # validate score range and format
        if record.get("score"):
            try:
                score = float(record["score"])
                if not (0 <= score <= 100):
                    errors.append("score must be between 0 and 100")
            except ValueError:
                errors.append("score must be a valid number")

        # validate credit hours format
        if record.get("credit_hours"):
            try:
                credit_hours = int(record["credit_hours"])
                if credit_hours <= 0:
                    errors.append("credit hours must be a positive integer")
            except ValueError:
                errors.append("credit hours must be an integer")
                
        # validate year of study
        if record.get("year_of_study"):
            try:
                year = int(record["year_of_study"])
                if not (1 <= year <= 10):  # reasonable range for year of study
                    errors.append("year of study must be between 1 and 10")
            except ValueError:
                errors.append("year of study must be an integer")

    except Exception as e:
        errors.append(f"validation error: {str(e)}")
        logger.error(f"error during field validation: {e}")

    return len(errors) == 0, errors

def read_student_records(file_path):
    """read and validate student records from csv or txt file"""
    valid_records = []
    errors = []
    
    logger.info(f"attempting to read student records from: {file_path}")

    # check if file exists
    if not os.path.exists(file_path):
        error_msg = f"file does not exist: {file_path}"
        errors.append(error_msg)
        logger.error(error_msg)
        return [], errors

    # check file size to avoid processing very large files
    try:
        file_size = os.path.getsize(file_path)
        if file_size > 10 * 1024 * 1024:  # 10mb limit
            error_msg = f"file too large: {file_size} bytes (max 10mb)"
            errors.append(error_msg)
            logger.error(error_msg)
            return [], errors
    except Exception as e:
        error_msg = f"error checking file size: {e}"
        errors.append(error_msg)
        logger.error(error_msg)

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            ext = os.path.splitext(file_path)[1].lower()
            logger.info(f"processing file with extension: {ext}")
            
            # determine file format and create appropriate reader
            if ext == '.csv':
                reader = csv.DictReader(f)
            elif ext == '.txt':
                reader = csv.DictReader(f, delimiter='\t')
            else:
                error_msg = f"unsupported file format: {ext}. use csv or txt files only."
                errors.append(error_msg)
                logger.error(error_msg)
                return [], errors

            # validate headers
            fieldnames = reader.fieldnames
            if not fieldnames:
                error_msg = "no headers found in file"
                errors.append(error_msg)
                logger.error(error_msg)
                return [], errors
                
            # check for missing required headers
            missing_headers = []
            for required_field in REQUIRED_FIELDS:
                if required_field not in fieldnames:
                    missing_headers.append(required_field)
                    
            if missing_headers:
                error_msg = f"missing required headers: {', '.join(missing_headers)}"
                errors.append(error_msg)
                logger.error(error_msg)
                return [], errors

            # process each row
            total_rows = 0
            for i, row in enumerate(reader, start=1):
                total_rows += 1
                
                # clean up the row data
                try:
                    record = {k.strip(): v.strip() if v else '' for k, v in row.items()}
                    
                    # validate the record
                    is_valid, validation_errors = validate_record_fields(record)
                    if is_valid:
                        valid_records.append(record)
                        logger.debug(f"valid record found on line {i}: {record['index_number']}")
                    else:
                        error_msg = f"line {i}: " + "; ".join(validation_errors)
                        errors.append(error_msg)
                        logger.warning(f"invalid record on line {i}: {validation_errors}")
                        
                except Exception as e:
                    error_msg = f"line {i}: error processing row - {str(e)}"
                    errors.append(error_msg)
                    logger.error(f"error processing row {i}: {e}")

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
        logger.error(f"unexpected error reading {file_path}: {e}")

    logger.info(f"file processing complete: {len(valid_records)} valid records, {len(errors)} errors")
    return valid_records, errors
