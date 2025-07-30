# 🚀 Enhanced SRMS Quick Start Guide

## Getting Started with Course and Semester Management

### Step 1: Initialize Enhanced System

**Option A: Using CLI**
1. Run the main application: `python main.py`
2. Login as admin
3. Select **9. 🎓 Enhanced Course & Semester Management**
4. Select **10. 🚀 Initialize Enhanced System**

**Option B: Using API**
```bash
curl -X POST http://localhost:8000/api/v1/system/initialize-enhanced
```

### Step 2: Add Your First Course

**CLI Method:**
1. From Enhanced Management menu, select **1. 📖 Add New Course**
2. Enter course details:
   ```
   Course Code: CS101
   Course Title: Introduction to Programming
   Credit Hours: 3
   Department: Computer Science
   Instructor: Dr. Smith
   ```

**API Method:**
```bash
curl -X POST http://localhost:8000/api/v1/courses \
  -H "Content-Type: application/json" \
  -d '{
    "course_code": "CS101",
    "course_title": "Introduction to Programming", 
    "credit_hours": 3,
    "department": "Computer Science",
    "instructor": "Dr. Smith"
  }'
```

### Step 3: Set Up Academic Calendar

**CLI Method:**
1. From Enhanced Management menu, select **6. 📅 Add New Semester**
2. Enter semester details:
   ```
   Semester ID: FALL2024
   Semester Name: Fall 2024
   Academic Year: 2024-2025
   Start Date: 2024-08-26
   End Date: 2024-12-15
   Set as current: y
   ```

**API Method:**
```bash
curl -X POST http://localhost:8000/api/v1/semesters \
  -H "Content-Type: application/json" \
  -d '{
    "semester_id": "FALL2024",
    "semester_name": "Fall 2024",
    "academic_year": "2024-2025",
    "start_date": "2024-08-26",
    "end_date": "2024-12-15",
    "is_current": true
  }'
```

### Step 4: Verify Setup

**CLI Method:**
- Select **11. 📊 System Dashboard** from Enhanced Management menu

**API Method:**
```bash
curl http://localhost:8000/api/v1/summary/dashboard
```

## 🎯 Common Operations

### Managing Courses

**View All Courses:**
```bash
# CLI: Enhanced Management → View All Courses
# API: GET /api/v1/courses
curl http://localhost:8000/api/v1/courses
```

**Search for a Course:**
```bash
# CLI: Enhanced Management → Search Course
# API: GET /api/v1/courses/search/{query}
curl http://localhost:8000/api/v1/courses/search/CS
```

**Update a Course:**
```bash
# CLI: Enhanced Management → Edit Course
# API: PUT /api/v1/courses/{course_code}
curl -X PUT http://localhost:8000/api/v1/courses/CS101 \
  -H "Content-Type: application/json" \
  -d '{"instructor": "Dr. Johnson"}'
```

### Managing Semesters

**View Current Semester:**
```bash
# CLI: Enhanced Management → View Current Semester
# API: GET /api/v1/semesters/current
curl http://localhost:8000/api/v1/semesters/current
```

**Change Current Semester:**
```bash
# CLI: Enhanced Management → Set Current Semester
# API: PUT /api/v1/semesters/{semester_id}/set-current
curl -X PUT http://localhost:8000/api/v1/semesters/SPRING2025/set-current
```

## 🔧 API Server Setup

1. **Start the API server:**
   ```bash
   cd backend
   python main.py --api
   ```

2. **Access API documentation:**
   - Open browser to `http://localhost:8000/docs`
   - Interactive API documentation available

## 📊 Sample Data Setup

Here's a quick script to populate your system with sample data:

```python
import requests

base_url = "http://localhost:8000/api/v1"

# Add sample courses
courses = [
    {"course_code": "CS101", "course_title": "Intro to Programming", "credit_hours": 3, "department": "CS"},
    {"course_code": "MATH101", "course_title": "Calculus I", "credit_hours": 4, "department": "Mathematics"},
    {"course_code": "ENG101", "course_title": "English Composition", "credit_hours": 3, "department": "English"}
]

for course in courses:
    response = requests.post(f"{base_url}/courses", json=course)
    print(f"Added course: {course['course_code']}")

# Add sample semesters
semesters = [
    {"semester_id": "FALL2024", "semester_name": "Fall 2024", "academic_year": "2024-2025", "is_current": True},
    {"semester_id": "SPRING2025", "semester_name": "Spring 2025", "academic_year": "2024-2025", "is_current": False}
]

for semester in semesters:
    response = requests.post(f"{base_url}/semesters", json=semester)
    print(f"Added semester: {semester['semester_id']}")
```

## 🐛 Troubleshooting

### Database Connection Issues
1. Verify PostgreSQL is running
2. Check connection settings in `config.py`
3. Ensure database exists and credentials are correct

### Import Errors
1. Ensure all dependencies are installed: `pip install -r requirements.txt`
2. Check Python path includes the backend directory

### API Not Starting
1. Check if port 8000 is available
2. Verify FastAPI is installed
3. Check logs for detailed error messages

## 📚 Next Steps

1. **Explore the CLI interface** - Familiarize yourself with all menu options
2. **Try the API endpoints** - Use the interactive docs at `/docs`
3. **Add real course data** - Start building your course catalog
4. **Set up academic calendar** - Create semesters for your institution
5. **Review documentation** - Check `ENHANCED_FEATURES.md` for complete details

## 🎉 You're Ready!

Your enhanced SRMS is now ready for comprehensive course and semester management. The system provides both user-friendly CLI interfaces and powerful API endpoints for integration with other systems.

**Need help?** Check the full documentation in `ENHANCED_FEATURES.md` or review the code examples in the test files.
