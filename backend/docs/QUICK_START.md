# 🚀 SRMS v2.0 Quick Start Guide

**Get your Student Result Management System up and running in 10 minutes!**

## 📋 Prerequisites

- Python 3.8+ installed
- PostgreSQL 12+ running
- Git (for cloning)

## ⚡ Quick Installation

### Step 1: Get the Code
```bash
git clone https://github.com/naeemAbdul-Aziz/srm-tool-python.git
cd srm-tool-python/backend
pip install -r requirements.txt
```

### Step 2: Configure Database
Edit `config.py` or create `.env` file:
```env
DB_NAME=srms_db
DB_USER=your_username
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

### Step 3: Initialize System

**🖥️ Start CLI Interface:**
```bash
python main.py
```

**📝 Setup Process:**
1. Select **"2. Sign Up"** 
2. Create admin account (username: admin, role: admin)
3. Select **"1. Login"** with admin credentials
4. Navigate to **"9. 🎓 Enhanced Course & Semester Management"**
5. Select **"3. Initialize Enhanced System"**
6. ✅ System initialized with enhanced database tables!

## 🎯 Core Setup (5 Minutes)

### Step 4: Add Your First Course

**CLI Method:**
1. From main menu: **"9. Enhanced Management"** → **"1. Course Management"**
2. Select **"2. Add new course"**
3. Enter details:
   ```
   Course Code: CS101
   Course Title: Introduction to Programming
   Credit Hours: 3
   Department: Computer Science
   Instructor: Dr. Smith
   Description: Basic programming concepts
   ```

### Step 5: Set Up Academic Calendar

**CLI Method:**
1. From Enhanced Management: **"2. Semester Management"**
2. Select **"2. Add new semester"**
3. Enter details:
   ```
   Semester ID: FALL2025
   Semester Name: Fall 2025
   Academic Year: 2025-2026
   Start Date: 2025-08-15
   End Date: 2025-12-15
   Set as current: y
   ```

### Step 6: Add Your First Student

**CLI Method:**
1. Main menu: **"6. Add a single student record"**
2. Enter student details:
   ```
   Index Number: STU001
   Full Name: John Smith
   Program: Computer Science
   Year of Study: 1
   Contact Info: john@email.com
   Course: CS101
   Score: 95
   ```

## 🌐 API Server Setup (Optional)

### Start API Server
```bash
# In a new terminal
cd backend
python api.py
```

**🔗 Access Points:**
- **API Base**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

### Test API with Sample Requests

**Add Course via API:**
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
**Add Course via API:**
```bash
curl -X POST http://localhost:8000/courses/ \
  -H "Content-Type: application/json" \
  -d '{
    "course_code": "CS101",
    "course_title": "Introduction to Programming", 
    "credit_hours": 3,
    "department": "Computer Science",
    "instructor": "Dr. Smith"
  }'
```

**Add Semester via API:**
```bash
curl -X POST http://localhost:8000/semesters/ \
  -H "Content-Type: application/json" \
  -d '{
    "semester_id": "FALL2025",
    "semester_name": "Fall 2025",
    "academic_year": "2025-2026",
    "start_date": "2025-08-15",
    "end_date": "2025-12-15",
    "is_current": true
  }'
```

**Add Student via API:**
```bash
curl -X POST http://localhost:8000/students/ \
  -H "Content-Type: application/json" \
  -d '{
    "index_number": "STU001",
    "full_name": "John Smith",
    "course": "CS101",
    "score": 95,
    "program": "Computer Science",
    "year_of_study": 1,
    "contact_info": "john@email.com"
  }'
```

## ✅ Verify Your Setup

### CLI Verification
1. Main menu → **"1. View all student records"** (should show John Smith)
2. Enhanced Management → **"1. Course Management"** → **"1. List all courses"** (should show CS101)
3. Enhanced Management → **"2. Semester Management"** → **"4. View current semester"** (should show Fall 2025)

### API Verification
```bash
# Check students
curl http://localhost:8000/students/

# Check courses  
curl http://localhost:8000/courses/

# Check current semester
curl http://localhost:8000/semesters/current
```

## 🎯 Common Operations

### 📚 Course Management

**View All Courses:**
```bash
# CLI: Enhanced Management → Course Management → List all courses
# API:
curl http://localhost:8000/courses/
```

**Search for a Course:**
```bash
# CLI: Enhanced Management → Course Management → Search course
# API:
curl http://localhost:8000/courses/CS101
```

**Update a Course:**
```bash
# CLI: Enhanced Management → Course Management → Edit course
# API:
curl -X PUT http://localhost:8000/courses/CS101 \
  -H "Content-Type: application/json" \
  -d '{"instructor": "Dr. Johnson"}'
```

### 📅 Semester Management

**View Current Semester:**
```bash
# CLI: Enhanced Management → Semester Management → View current semester
# API:
curl http://localhost:8000/semesters/current
```

**Change Current Semester:**
```bash
# CLI: Enhanced Management → Semester Management → Set current semester
# API:
curl -X PUT http://localhost:8000/semesters/SPRING2026/set-current
```

### �‍🎓 Student Operations

**View Student Details:**
```bash
# CLI: Main Menu → View student by index number
# API:
curl http://localhost:8000/students/STU001
```

**Update Student Grade:**
```bash
# CLI: Main Menu → Update student score
# API:
curl -X PUT http://localhost:8000/students/STU001 \
  -H "Content-Type: application/json" \
  -d '{"score": 88, "course_code": "CS101"}'
```

**Generate Student Transcript:**
```bash
# CLI: Main Menu → Export summary report to PDF/TXT
# API:
curl http://localhost:8000/export/STU001/pdf > transcript.pdf
```

## 📊 Bulk Operations

### Bulk Student Import

**Prepare CSV File** (`students.csv`):
```csv
index_number,name,email,program,year,course,grade,score
STU002,Jane Doe,jane@email.com,Mathematics,1,MATH101,A,92
STU003,Bob Wilson,bob@email.com,Physics,2,PHY201,B+,87
STU004,Alice Brown,alice@email.com,Chemistry,1,CHEM101,A-,90
```

**Import via CLI:**
1. Main menu → **"8. Bulk Import Student Records"**
2. Upload the CSV file
3. Review import summary

**Import via API:**
```bash
curl -X POST http://localhost:8000/students/upload \
  -F "file=@students.csv"
```

## 🔧 Advanced Configuration

## � Advanced Configuration

### Environment Variables (.env file)
```env
# Database Configuration
DB_NAME=srms_production
DB_USER=srms_admin
DB_PASSWORD=secure_password
DB_HOST=localhost
DB_PORT=5432

# Security
SECRET_KEY=your-secret-key-here

# API Configuration (optional)
API_HOST=0.0.0.0
API_PORT=8000
```

### Production Deployment
```bash
# For production API deployment
python api.py --host 0.0.0.0 --port 8000

# Or with gunicorn
pip install gunicorn
gunicorn api:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📊 Sample Data Setup

**Quick populate script** (`populate_sample_data.py`):
```python
import requests

base_url = "http://localhost:8000"

# Sample courses
courses = [
    {"course_code": "CS101", "course_title": "Intro to Programming", "credit_hours": 3, "department": "CS"},
    {"course_code": "MATH101", "course_title": "Calculus I", "credit_hours": 4, "department": "Mathematics"},
    {"course_code": "ENG101", "course_title": "English Composition", "credit_hours": 3, "department": "English"},
    {"course_code": "PHY101", "course_title": "Physics I", "credit_hours": 4, "department": "Physics"}
]

# Sample semesters
semesters = [
    {"semester_id": "FALL2025", "semester_name": "Fall 2025", "academic_year": "2025-2026", "is_current": True},
    {"semester_id": "SPRING2026", "semester_name": "Spring 2026", "academic_year": "2025-2026", "is_current": False}
]

# Add data
for course in courses:
    response = requests.post(f"{base_url}/courses/", json=course)
    print(f"Added course: {course['course_code']}")

for semester in semesters:
    response = requests.post(f"{base_url}/semesters/", json=semester)
    print(f"Added semester: {semester['semester_id']}")
```

**Run the script:**
```bash
python populate_sample_data.py
```

## 🐛 Troubleshooting

### Common Issues & Solutions

**Database Connection Failed:**
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql  # Linux
brew services list | grep postgres  # macOS

# Verify credentials in config.py
# Test connection manually
```

**Import Errors:**
```bash
# Ensure all dependencies installed
pip install -r requirements.txt

# Check Python version
python --version  # Should be 3.8+

# Verify working directory
pwd  # Should be in /backend folder
```

**API Server Won't Start:**
```bash
# Check if port 8000 is in use
netstat -an | grep 8000  # Windows/Linux
lsof -i :8000  # macOS

# Try different port
python api.py --port 8001
```

**Enhanced System Not Initializing:**
1. Ensure you're logged in as admin
2. Check database permissions
3. Verify PostgreSQL version (12+)
4. Check logs in `app.log` file

### Error Logs
Check the `app.log` file for detailed error information:
```bash
tail -f app.log  # Follow logs in real-time
grep ERROR app.log  # Find error messages
```

## 🎯 Next Steps

### Immediate Actions
1. ✅ **Add more courses** - Build your course catalog
2. ✅ **Create academic calendar** - Set up all semesters for the year
3. ✅ **Import student data** - Use bulk import for efficiency
4. ✅ **Test all features** - Verify everything works as expected

### Advanced Setup
1. **🔒 Security hardening** - Change default passwords, configure SSL
2. **📊 Monitoring setup** - Configure logging and monitoring
3. **🔄 Backup procedures** - Set up automated database backups
4. **🌐 Web integration** - Develop frontend using the API

### Integration Opportunities
1. **LMS Integration** - Connect with Learning Management Systems
2. **Mobile App** - Build mobile apps using the API
3. **Parent Portal** - Create parent/guardian access
4. **Financial Systems** - Integrate with fee management

## 📚 Additional Resources

### Documentation
- **[Official Documentation](OFFICIAL_SYSTEM_DOCUMENTATION.md)** - Complete system guide
- **[Enhanced Features](ENHANCED_FEATURES.md)** - Detailed feature documentation
- **[Usage Guide](USAGE_GUIDE.md)** - Step-by-step instructions

### API Resources
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Spec**: http://localhost:8000/openapi.json

### Support
- **GitHub Issues**: Report bugs and request features
- **Documentation**: Check docs folder for detailed guides
- **Community**: Join discussions for help and tips

## 🎉 You're All Set!

Your SRMS v2.0 is now fully operational! You have:

✅ **Complete student management system**  
✅ **Course and semester management**  
✅ **Professional reporting capabilities**  
✅ **API integration ready**  
✅ **Production-grade security**  

**🚀 Ready to manage your educational institution's academic records efficiently!**

---

**Need help?** Check the comprehensive documentation or open an issue on GitHub.  
**Want more features?** The system is designed for easy extension and customization!
