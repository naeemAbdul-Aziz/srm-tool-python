# 🎓 Student Result Management System (SRMS)

**A comprehensive, production-ready academic management platform with dual CLI/API interface**

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/naeemAbdul-Aziz/srm-tool-python)
[![Status](https://img.shields.io/badge/status-production--ready-green.svg)](https://github.com/naeemAbdul-Aziz/srm-tool-python)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

## 🌟 Overview

SRMS is a complete Student Result Management System designed for educational institutions. It provides comprehensive academic lifecycle management from enrollment through graduation with **dual interface architecture**:

- **🖥️ CLI Interface** - Interactive command-line for admin and student operations
- **🌐 REST API** - FastAPI-based endpoints for web/mobile integration

## ✨ Key Features

### 👨‍💼 **Admin Capabilities**
- Complete student profile management (CRUD operations)
- Course and semester administration
- Bulk grade import from CSV files
- Comprehensive reporting (PDF/TXT transcripts)
- User account management with automatic password generation
- Analytics dashboard and grade distribution reports

### 👨‍🎓 **Student Capabilities**
- View personal profile and academic records
- Access grades with filtering by semester/year
- Real-time GPA calculation with breakdowns
- Download academic transcripts

### 🔒 **Security Features**
- bcrypt password hashing with salt
- Role-based access control (Admin/Student)
- Session management with configurable timeouts
- Environment-based configuration for sensitive data
- Comprehensive audit logging

## 📁 Project Structure

```
srm-tool-python/
├── backend/
│   ├── main.py                 # CLI application entry point
│   ├── api.py                  # FastAPI server with all endpoints
│   ├── menu.py                 # Interactive CLI menu system
│   ├── course_management.py    # Course & semester management CLI
│   ├── db.py                   # Database operations & schema
│   ├── auth.py                 # Authentication & user management
│   ├── bulk_importer.py        # CSV bulk import functionality
│   ├── report_utils.py         # PDF/TXT report generation
│   ├── grade_util.py           # Grade calculations & analytics
│   ├── logger.py               # Color-coded logging system
│   ├── session.py              # Session management
│   ├── config.py               # Configuration management
│   ├── seed_data.py            # Database seeding utilities
│   ├── requirements.txt        # Python dependencies
│   ├── .env.example            # Environment template
│   └── docs/                   # Additional documentation
└── frontend/
    └── index.html              # Basic web interface template
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- Git

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/naeemAbdul-Aziz/srm-tool-python.git
   cd srm-tool-python/backend
   ```

2. **Set up virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

4. **Start the application:**
   ```bash
   # CLI Interface
   python main.py
   
   # API Server
   python -m uvicorn api:app --host 0.0.0.0 --port 8000 --reload
   ```

## 👥 Complete User Flow Guide

### 🔧 **Initial System Setup**

1. **Start CLI Application:**
   ```bash
   python main.py
   ```

2. **Create Admin Account:**
   - Select `2. Sign Up`
   - Enter admin credentials:
     - Username: `admin`
     - Password: `your_secure_password`
     - Role: `admin`

3. **Login as Admin:**
   - Select `1. Login`
   - Enter admin credentials

4. **Initialize System:**
   - Select `9. 🎓 Enhanced Course & Semester Management`
   - Select `3. Initialize Enhanced System`
   - System creates all database tables

### 👨‍💼 **Admin Workflow**

#### **Course & Semester Management:**
1. Navigate to `9. Enhanced Course & Semester Management`
2. **Add Courses:**
   - Select `1. Course Management` → `1. Add New Course`
   - Enter: Course Code, Title, Credit Hours
3. **Create Semesters:**
   - Select `2. Semester Management` → `1. Add New Semester`
   - Enter: Semester Name, Start/End Dates

#### **Student Management:**
1. **Add Students:**
   - Select `3. Student Management` → `1. Add Student Profile`
   - Enter student details (Index Number, Name, Email, etc.)

2. **Create Student Accounts:**
   - Select `7. User Management` → `3. Create Student Account`
   - Enter Index Number and Full Name
   - **System automatically generates secure password**
   - Password displayed once for distribution to student

#### **Grade Management:**
1. **Individual Grade Entry:**
   - Select `4. Grade Management` → `1. Add Grade`
   - Choose student, course, semester
   - Enter score (system calculates letter grade and GPA points)

2. **Bulk Grade Import:**
   - Prepare CSV file with columns: `index_number,course_code,score`
   - Select `5. Bulk Data Import` → `1. Import from CSV`
   - Choose file and semester
   - System processes and validates all entries

#### **Reporting & Analytics:**
1. **Generate Reports:**
   - Select `6. Reports & Analytics` → `1. Generate Summary Report`
   - Choose format: PDF, TXT, or Console
   - Select filters: Semester, Student, etc.

2. **View Analytics:**
   - Select `6. Reports & Analytics` → `2. Show Grade Distribution`
   - View grade statistics and performance trends

### 👨‍🎓 **Student Workflow**

1. **Login:**
   - Start CLI: `python main.py`
   - Select `1. Login`
   - Enter credentials provided by admin

2. **View Profile:**
   - Select `2. View Student Profile`
   - See personal information and enrollment details

3. **Check Grades:**
   - Select `3. View Student Grades`
   - See all grades with letter grades and GPA points
   - Filter by semester or academic year

4. **Calculate GPA:**
   - Select `4. Calculate GPA`
   - View cumulative or semester-specific GPA
   - See detailed breakdown by course

5. **Generate Transcript:**
   - Select `5. Generate Academic Transcript`
   - Download PDF or TXT format

## 🔐 Security & Authentication

### **Password Management:**
- **Admin passwords:** Manually set during account creation
- **Student passwords:** Automatically generated (8-character secure passwords)
- **Password security:** bcrypt hashing with salt
- **Legacy support:** Automatic migration from old SHA256 hashes

### **Session Management:**
- Configurable session timeouts
- Automatic session expiry
- Activity tracking
- Secure logout functionality

### **Role-Based Access:**
- **Admin role:** Full system access
- **Student role:** Limited to personal data access
- **API endpoints:** Protected with HTTP Basic Authentication

## 🌐 API Documentation

### **Start API Server:**
```bash
python -m uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

### **Access Documentation:**
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### **Key Endpoints:**

#### **Authentication Required (HTTP Basic):**
```
GET  /health                    # System health check
GET  /courses                   # List all courses
GET  /semesters                 # List all semesters
```

#### **Admin Endpoints:**
```
POST /admin/students            # Create student profile
GET  /admin/students            # List all students (paginated)
GET  /admin/students/{index}    # Get specific student
PUT  /admin/students/{index}    # Update student profile

POST /admin/courses             # Create course
GET  /admin/courses             # List courses (paginated)

POST /admin/semesters           # Create semester
GET  /admin/semesters           # List semesters

POST /admin/grades              # Create/update grades
GET  /admin/grades              # List grades (filtered)

POST /admin/users               # Create user account
POST /admin/student-accounts    # Create student account
POST /admin/reset-password      # Reset student password

POST /admin/bulk-import         # Bulk import from CSV
GET  /admin/reports/summary     # Generate reports
GET  /admin/analytics/dashboard # Dashboard analytics
```

#### **Student Endpoints:**
```
GET  /student/profile           # Get own profile
GET  /student/grades            # Get own grades (filtered)
GET  /student/gpa               # Calculate GPA
```

## 📊 Database Schema

### **Core Tables:**
- **students** - Student profile information
- **courses** - Course catalog
- **semesters** - Academic calendar
- **grades** - Grade records with GPA calculations
- **users** - Authentication credentials

### **Key Features:**
- Foreign key relationships
- Data validation constraints
- Automatic timestamp tracking
- Optimized indexing for performance

## 🔧 Configuration

### **Environment Variables (.env):**
```env
# Database Configuration
DB_NAME=srms_production
DB_USER=your_db_user
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=5432

# Application Configuration
APP_DEBUG=False
LOG_LEVEL=INFO

# Security Configuration
SECRET_KEY=your_32_character_secret_key_here
SESSION_TIMEOUT=3600
```

## 📝 Logging & Monitoring

### **Log Features:**
- Color-coded console output for development
- File-based logging (`app.log`) for production
- Configurable log levels (DEBUG, INFO, WARNING, ERROR)
- Comprehensive audit trail for all operations

### **Monitoring Points:**
- User authentication attempts
- Database operations
- Grade modifications
- System errors and exceptions
- API request/response cycles

## 🔄 Bulk Operations

### **CSV Import Format:**
```csv
index_number,course_code,score,semester_name,academic_year
STU001,CS101,85,Fall 2024,2024/2025
STU002,CS101,92,Fall 2024,2024/2025
```

### **Supported Operations:**
- Student profile bulk creation
- Grade bulk import with validation
- Course enrollment management
- Semester grade processing

## 📈 Reporting Capabilities

### **Available Reports:**
1. **Student Transcripts** (PDF/TXT)
2. **Grade Distribution Analysis**
3. **Semester Performance Summaries**
4. **Course Analytics**
5. **System Usage Statistics**

### **Export Formats:**
- **PDF:** Professional transcripts with formatting
- **TXT:** Plain text for system integration
- **JSON:** API responses for web applications
- **CSV:** Data export for external analysis

## 🛡️ Production Deployment

### **Security Checklist:**
- [ ] Environment variables configured
- [ ] Strong database passwords
- [ ] DEBUG mode disabled
- [ ] Firewall configured
- [ ] Regular backups scheduled
- [ ] SSL/TLS certificates installed
- [ ] Log rotation configured

### **Performance Optimization:**
- Database connection pooling
- Efficient query optimization
- Proper indexing strategy
- Session timeout management
- Log file rotation

## 🆘 Troubleshooting

### **Common Issues:**

1. **Database Connection Failed:**
   - Check credentials in `.env` file
   - Verify PostgreSQL service is running
   - Confirm database exists

2. **Import Errors:**
   - Ensure all dependencies installed: `pip install -r requirements.txt`
   - Check Python version compatibility (3.8+)

3. **Authentication Issues:**
   - Verify user credentials
   - Check session timeout settings
   - Review log files for detailed errors

4. **Permission Denied:**
   - Check file system permissions
   - Verify database user privileges
   - Review role assignments

### **Log Analysis:**
Check `app.log` for detailed error information with timestamps and stack traces.

## 📞 Support & Contributing

### **Getting Help:**
1. Check the troubleshooting section above
2. Review log files for error details
3. Verify configuration settings
4. Test with sample data

### **Development:**
- Python 3.8+ required
- PostgreSQL 12+ recommended
- Follow PEP 8 coding standards
- Comprehensive testing encouraged

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Built with ❤️ for educational institutions worldwide**
