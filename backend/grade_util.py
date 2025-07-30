# grade_util.py
"""
Robust GPA/CGPA calculation and grade utility functions with logging.
"""

import logging
from logger import get_logger

logger = get_logger(__name__)

def calculate_grade(score):
    """Returns the letter grade based on numeric score."""
    try:
        score = int(score)
        if score >= 80:
            return 'A'
        elif score >= 70:
            return 'B'
        elif score >= 60:
            return 'C'
        elif score >= 50:
            return 'D'
        else:
            return 'F'
    except (ValueError, TypeError) as e:
        logger.error(f"Invalid score '{score}' passed to calculate_grade: {e}")
        return 'F'  # default fail grade on error

def summarize_grades(student_list):
    """Returns count of each grade in a summary dictionary."""
    summary = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0}
    for student in student_list:
        grade = student.get('grade')
        if grade in summary:
            summary[grade] += 1
        else:
            logger.warning(f"Unknown grade '{grade}' found in record: {student}")
    return summary

def calculate_gpa(grades, scale=4.0):
    """
    Calculate GPA from a list of dictionaries:
    grades = [{ 'score': 85, 'credit': 3 }, { 'score': 74, 'credit': 2 }]
    """
    try:
        total_quality_points = 0.0
        total_credits = 0

        for g in grades:
            score = g.get('score')
            credit = g.get('credit', 0)

            if score is None or credit <= 0:
                logger.warning(f"Skipping grade record due to invalid input: {g}")
                continue

            grade_point = get_grade_point(score, scale)
            total_quality_points += grade_point * credit
            total_credits += credit

        if total_credits == 0:
            logger.warning("No valid credits found for GPA calculation.")
            return 0.0

        gpa = round(total_quality_points / total_credits, 2)
        logger.info(f"Calculated GPA: {gpa} on {scale} scale")
        return gpa

    except Exception as e:
        logger.error(f"Failed to calculate GPA: {e}")
        return 0.0

def get_grade_point(score, scale=4.0):
    """Map score to grade points based on scale."""
    try:
        score = int(score)
        if scale == 5.0:
            if score >= 80: return 5.0
            elif score >= 70: return 4.0
            elif score >= 60: return 3.0
            elif score >= 50: return 2.0
            else: return 1.0
        else:  # default 4.0 scale
            if score >= 80: return 4.0
            elif score >= 70: return 3.0
            elif score >= 60: return 2.0
            elif score >= 50: return 1.0
            else: return 0.0
    except (ValueError, TypeError) as e:
        logger.error(f"Invalid score '{score}' for grade point mapping: {e}")
        return 0.0
