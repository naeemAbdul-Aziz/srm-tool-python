# file format IndexNumber, FullName, Course, Score
# 12345678, John Doe, CS101, 85

import os
import csv
from venv import logger
from logger import get_logger
from utils import calculate_grade
from db import insert_student_record

logger = get_logger(__name__)

def is_valid_record(fields):
    """
    checks if the record has exactly 4 parts
    and the score can be converted to an integer

    “first make sure the line has 4 parts, then try converting the score. If either fails, reject the record.”

    """
    if len(fields) != 4:
        return False
    try:
        int(fields[3])  # test if score is an integer
        return True
    except ValueError:
        return False

def parse_record(fields):
    """
    takes the list of fields and returns a cleaned student dictionary with grade
    """
    index_number = fields[0]
    full_name = fields[1]
    course = fields[2]
    score = int(fields[3])
    grade = calculate_grade(score)

    return {
        "index_number": index_number,
        "full_name": full_name,
        "course": course,
        "score": score,
        "grade": grade
    }


def read_student_file(file_path):
    """
    reads a student .txt or .csv file and returns a list of valid student dictionaries.
    """

    students = []  # initialize an empty list to hold student data



    #check if the file exists
    if not os.path.isfile(file_path):
        logger.error(f"File not found: {file_path}")
        return students  # return empty list if file does not exist
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()  # read all lines from the file

            for line_number, line in enumerate(lines, start=1):
                line = line.strip() #remove leading and trailing whitespace
                if not line:  # skip empty lines    
                    continue

                parts = line.split(',')  # split the line by comma

                if not is_valid_record(parts):  # check if the record is valid
                    logger.warning(f"Invalid format on line {line_number}: {line}")
                    continue  # skip invalid records

                try:
                    student = parse_record(parts)  # parse the record into a dictionary
                    students.append(student)  # add the student dictionary to the list
                except Exception as e:
                    logger.error(f"Error parsing line {line_number}: {e}")
                    continue
    except FileNotFoundError:
        logger.error(f'file {file_path} not found.')
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
    return students  # return the list of student dictionaries

def read_student_records(file_path):
    """
    Reads student records from a CSV or TXT file.
    Each line should have: IndexNumber, FullName, Course, Score.
    Returns a list of valid records and a list of errors.
    """
    valid_records = []
    errors = []

    try:
        with open(file_path, "r") as f:
            reader = csv.reader(f)
            for i, row in enumerate(reader):
                if len(row) != 4:
                    errors.append(f"Line {i + 1}: Invalid format - {row}")
                    continue

                index_number, full_name, course, score = row
                if not index_number.isdigit() or not score.isdigit():
                    errors.append(f"Line {i + 1}: Invalid data - {row}")
                    continue

                valid_records.append({
                    "index_number": index_number,
                    "full_name": full_name,
                    "course": course,
                    "score": int(score),
                })
    except Exception as e:
        errors.append(f"Error reading file: {e}")

    return valid_records, errors

def process_file_and_insert(file_path):
    """
    Reads student records from file and inserts them into the configured database.
    Only to be called from the GUI.
    """
    from db import connect_to_db
    conn = connect_to_db()
    if conn is None:
        logger.error("Failed to connect to the database for file upload.")
        return 0
    students = read_student_file(file_path)
    inserted_count = 0
    for student in students:
        try:
            insert_student_record(conn, student)
            inserted_count += 1
        except Exception as e:
            logger.error(f"Error inserting student record {student.get('index_number', 'Unknown')}: {e}")
            continue
    try:
        conn.close()
    except Exception as e:
        logger.error(f"Error closing database connection: {e}")
    logger.info(f"Inserted {inserted_count} student record(s) from file upload.")
    return inserted_count
