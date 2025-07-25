# grading.py
"""
Functions for grade calculation and summary logic.
"""

def calculate_grade(score):
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


def summarize_grades(student_list):
    summary = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0}
    for student in student_list:
        grade = student['grade']
        if grade in summary:
            summary[grade] += 1
    return summary
