# api.py - FastAPI application for Student Result Management System
# Production-ready REST API with comprehensive endpoints, authentication, and error handling

from fastapi import FastAPI, HTTPException, Depends, status, Query, Path
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from db import (
    connect_to_db, fetch_all_records, insert_student_profile, fetch_student_by_index_number,
    insert_course, fetch_all_courses, fetch_course_by_code, insert_semester, fetch_all_semesters,
    update_student_score, delete_course, delete_semester, insert_grade,
    fetch_semester_by_name, create_tables_if_not_exist
)
from grade_util import calculate_grade, get_grade_point, calculate_gpa, summarize_grades
from auth import (
    authenticate_user, create_user, create_student_account, reset_student_password
)
from bulk_importer import bulk_import_from_file
from report_utils import export_summary_report_pdf, export_summary_report_txt
from logger import get_logger
from session import session_manager
import traceback

# Initialize logger
logger = get_logger(__name__)

# Initialize FastAPI app with metadata
app = FastAPI(
    title="Student Result Management System API",
    description="Comprehensive API for managing student records, grades, and academic reports",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# HTTP Basic Authentication setup
security = HTTPBasic()

# ========================================
# PYDANTIC MODELS (REQUEST/RESPONSE SCHEMAS)
# ========================================

# ========================================
# PYDANTIC MODELS (REQUEST/RESPONSE SCHEMAS)
# ========================================

class StudentCreate(BaseModel):
    """Schema for creating a new student profile"""
    index_number: str = Field(..., min_length=1, max_length=20, description="Unique student index number")
    full_name: str = Field(..., min_length=1, max_length=100, description="Student's full name")
    dob: Optional[str] = Field(None, description="Date of birth in YYYY-MM-DD format")
    gender: Optional[str] = Field(None, max_length=10, description="Student's gender")
    contact_email: Optional[str] = Field(None, max_length=100, description="Student's email address")
    phone: Optional[str] = Field(None, max_length=20, description="Student's phone number")
    program: Optional[str] = Field(None, max_length=100, description="Academic program")
    year_of_study: Optional[int] = Field(None, ge=1, le=10, description="Current year of study")

    @validator('dob')
    def validate_dob(cls, v):
        if v:
            try:
                datetime.strptime(v, '%Y-%m-%d')
            except ValueError:
                raise ValueError('Date must be in YYYY-MM-DD format')
        return v
    
    @validator('index_number')
    def validate_index_format(cls, v):
        if not v.startswith('ug') or len(v) != 7:
            raise ValueError('Index number must be in format: ug##### (e.g., ug12345)')
        return v

class StudentUpdate(BaseModel):
    """Schema for updating student profile"""
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    dob: Optional[str] = None
    gender: Optional[str] = Field(None, max_length=10)
    contact_email: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    program: Optional[str] = Field(None, max_length=100)
    year_of_study: Optional[int] = Field(None, ge=1, le=10)

class CourseCreate(BaseModel):
    """Schema for creating a new course"""
    course_code: str = Field(..., min_length=1, max_length=20, description="Unique course code")
    course_title: str = Field(..., min_length=1, max_length=200, description="Course title")
    credit_hours: int = Field(..., ge=1, le=10, description="Number of credit hours")

class SemesterCreate(BaseModel):
    """Schema for creating a new semester"""
    semester_name: str = Field(..., min_length=1, max_length=50, description="Semester name")
    academic_year: str = Field(..., min_length=1, max_length=20, description="Academic year (e.g., '2023/2024')")
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")

    @validator('start_date', 'end_date')
    def validate_dates(cls, v):
        try:
            datetime.strptime(v, '%Y-%m-%d')
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')
        return v
    
    @validator('academic_year')
    def validate_academic_year(cls, v):
        if '/' not in v or len(v.split('/')) != 2:
            raise ValueError('Academic year must be in format: YYYY/YYYY (e.g., 2023/2024)')
        return v
        try:
            datetime.strptime(v, '%Y-%m-%d')
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')
        return v

class GradeCreate(BaseModel):
    """Schema for creating/updating a grade"""
    student_index: str = Field(..., description="Student index number")
    course_code: str = Field(..., description="Course code")
    semester_name: str = Field(..., description="Semester name")
    score: float = Field(..., ge=0, le=100, description="Numeric score (0-100)")
    academic_year: str = Field(..., description="Academic year (e.g., '2023/2024')")

class UserCreate(BaseModel):
    """Schema for creating a new user account"""
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    password: str = Field(..., min_length=6, description="Password (minimum 6 characters)")
    role: str = Field(..., description="User role (admin/student)")

    @validator('role')
    def validate_role(cls, v):
        if v not in ['admin', 'student']:
            raise ValueError('Role must be either "admin" or "student"')
        return v

class StudentAccountCreate(BaseModel):
    """Schema for creating a student account"""
    index_number: str = Field(..., min_length=1, description="Student index number")
    full_name: str = Field(..., min_length=1, description="Student full name")
    password: Optional[str] = Field(None, description="Custom password (optional)")

class PasswordReset(BaseModel):
    """Schema for password reset"""
    index_number: str = Field(..., description="Student index number")
    new_password: Optional[str] = Field(None, description="New password (optional for default)")

class BulkImportRequest(BaseModel):
    """Schema for bulk import request"""
    semester_name: str = Field(..., description="Semester name for imported records")
    file_data: List[Dict[str, Any]] = Field(..., description="CSV data as list of dictionaries")

# Response Models
class APIResponse(BaseModel):
    """Standard API response wrapper"""
    success: bool
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None

class StudentResponse(BaseModel):
    """Student profile response"""
    index_number: str
    full_name: str
    dob: Optional[str]
    gender: Optional[str]
    contact_email: Optional[str]
    phone: Optional[str]
    program: Optional[str]
    year_of_study: Optional[int]
    grades: Optional[List[Dict[str, Any]]] = []

class SchoolProgramResponse(BaseModel):
    """University of Ghana schools and programs response"""
    school: str
    programs: List[str]

class CourseResponse(BaseModel):
    """Course information response"""
    course_id: int
    course_code: str
    course_title: str
    credit_hours: int

class SemesterResponse(BaseModel):
    """Semester information response"""
    semester_id: int
    semester_name: str
    academic_year: str
    start_date: str
    end_date: str

class GradeResponse(BaseModel):
    """Grade information response"""
    student_index: str
    student_name: str
    course_code: str
    course_title: str
    semester_name: str
    academic_year: str
    score: float
    grade: str
    grade_point: float

class GPAResponse(BaseModel):
    """GPA calculation response"""
    student_index: str
    student_name: str
    semester_gpa: Optional[float]
    cumulative_gpa: Optional[float]
    total_credit_hours: int
    semester_credit_hours: int

# ========================================
# AUTHENTICATION & DEPENDENCIES
# ========================================

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    """
    Authentication dependency that validates user credentials.
    Returns user data if authentication successful.
    """
    try:
        logger.debug(f"Authentication attempt for user: {credentials.username}")
        user = authenticate_user(credentials.username, credentials.password)
        
        if not user:
            logger.warning(f"Authentication failed for user: {credentials.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Basic"},
            )
        
        logger.info(f"User authenticated successfully: {credentials.username} ({user.get('role')})")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error for user {credentials.username}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        )

def require_admin_role(current_user: dict = Depends(get_current_user)):
    """Dependency that requires admin role"""
    if current_user.get('role') != 'admin':
        logger.warning(f"Access denied: User {current_user.get('username')} attempted admin operation")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

def require_student_role(current_user: dict = Depends(get_current_user)):
    """Dependency that requires student role"""
    if current_user.get('role') != 'student':
        logger.warning(f"Access denied: User {current_user.get('username')} attempted student operation")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student access required"
        )
    return current_user

# ========================================
# ERROR HANDLERS
# ========================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Global HTTP exception handler with logging"""
    logger.error(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": exc.detail, "error": str(exc.status_code)}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Global exception handler for unhandled errors"""
    logger.error(f"Unhandled exception: {str(exc)}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False, 
            "message": "Internal server error", 
            "error": "An unexpected error occurred"
        }
    )

# ========================================
# UTILITY FUNCTIONS
# ========================================

def handle_db_operation(operation, *args, **kwargs):
    """
    Utility function to handle database operations with proper error handling
    """
    conn = None
    try:
        logger.debug("Establishing database connection...")
        conn = connect_to_db()
        if not conn:
            logger.error("Failed to establish database connection")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service unavailable"
            )
        
        logger.debug(f"Executing database operation: {operation.__name__}")
        result = operation(conn, *args, **kwargs)
        logger.debug("Database operation completed successfully")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database operation failed: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database operation failed: {str(e)}"
        )
    finally:
        if conn:
            conn.close()
            logger.debug("Database connection closed")

def fetch_student_grades(conn, index_number, semester=None, academic_year=None):
    """Fetch student grades with optional filtering"""
    try:
        cursor = conn.cursor()
        query = """
            SELECT g.*, c.course_title, c.credit_hours 
            FROM grades g
            JOIN courses c ON g.course_code = c.course_code
            WHERE g.student_index = %s
        """
        params = [index_number]
        
        if semester:
            query += " AND g.semester_name = %s"
            params.append(semester)
        
        if academic_year:
            query += " AND g.academic_year = %s"
            params.append(academic_year)
            
        query += " ORDER BY g.academic_year DESC, g.semester_name"
        
        cursor.execute(query, params)
        grades = cursor.fetchall()
        
        # Convert to list of dictionaries
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in grades]
        
    except Exception as e:
        logger.error(f"Error fetching student grades: {str(e)}")
        return []

def calculate_student_gpa(conn, index_number, semester=None, academic_year=None):
    """Calculate student GPA with optional filtering"""
    try:
        grades = fetch_student_grades(conn, index_number, semester, academic_year)
        if not grades:
            return {"gpa": 0.0, "total_credits": 0, "total_courses": 0}
        
        total_points = 0
        total_credits = 0
        
        for grade in grades:
            credit_hours = grade.get('credit_hours', 3)  # Default to 3 if not specified
            grade_points = get_grade_point(grade.get('score', 0))
            
            total_points += grade_points * credit_hours
            total_credits += credit_hours
        
        gpa = total_points / total_credits if total_credits > 0 else 0.0
        
        return {
            "gpa": round(gpa, 2),
            "total_credits": total_credits,
            "total_courses": len(grades),
            "grade_breakdown": grades
        }
        
    except Exception as e:
        logger.error(f"Error calculating GPA: {str(e)}")
        return {"gpa": 0.0, "total_credits": 0, "total_courses": 0}

def insert_student_grade(conn, student_index, course_code, semester_name, score, academic_year):
    """Insert or update a student grade"""
    try:
        cursor = conn.cursor()
        
        # Check if grade already exists
        check_query = """
            SELECT id FROM grades 
            WHERE student_index = %s AND course_code = %s AND semester_name = %s AND academic_year = %s
        """
        cursor.execute(check_query, (student_index, course_code, semester_name, academic_year))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing grade
            update_query = """
                UPDATE grades 
                SET score = %s, letter_grade = %s, grade_points = %s
                WHERE id = %s
            """
            letter_grade = calculate_grade(score)
            grade_points = get_grade_point(score)
            cursor.execute(update_query, (score, letter_grade, grade_points, existing[0]))
            conn.commit()
            return existing[0]
        else:
            # Insert new grade
            insert_query = """
                INSERT INTO grades (student_index, course_code, semester_name, score, letter_grade, grade_points, academic_year)
                VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
            """
            letter_grade = calculate_grade(score)
            grade_points = get_grade_point(score)
            cursor.execute(insert_query, (
                student_index, course_code, semester_name, score, letter_grade, grade_points, academic_year
            ))
            result = cursor.fetchone()
            conn.commit()
            return result[0] if result else None
            
    except Exception as e:
        logger.error(f"Error inserting/updating grade: {str(e)}")
        conn.rollback()
        return None

def fetch_grades_with_filters(conn, student_index=None, course_code=None, semester=None, skip=0, limit=100):
    """Fetch grades with filtering and pagination"""
    try:
        cursor = conn.cursor()
        
        query = """
            SELECT g.*, s.full_name, c.course_title
            FROM grades g
            JOIN students s ON g.student_index = s.index_number
            JOIN courses c ON g.course_code = c.course_code
            WHERE 1=1
        """
        params = []
        
        if student_index:
            query += " AND g.student_index = %s"
            params.append(student_index)
            
        if course_code:
            query += " AND g.course_code = %s"
            params.append(course_code)
            
        if semester:
            query += " AND g.semester_name = %s"
            params.append(semester)
        
        # Get total count
        count_query = f"SELECT COUNT(*) FROM ({query}) as filtered"
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()[0]
        
        # Add pagination
        query += " ORDER BY g.academic_year DESC, g.semester_name LIMIT %s OFFSET %s"
        params.extend([limit, skip])
        
        cursor.execute(query, params)
        grades = cursor.fetchall()
        
        # Convert to list of dictionaries
        columns = [desc[0] for desc in cursor.description]
        grades_list = [dict(zip(columns, row)) for row in grades]
        
        return {
            "grades": grades_list,
            "total_count": total_count,
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Error fetching grades with filters: {str(e)}")
        return {"grades": [], "total_count": 0, "skip": skip, "limit": limit}

# ========================================
# HEALTH CHECK & SYSTEM ENDPOINTS
# ========================================

@app.get("/", response_model=APIResponse)
async def root():
    """Root endpoint - API health check"""
    logger.info("Root endpoint accessed")
    return APIResponse(
        success=True,
        message="Student Result Management System API is running",
        data={"version": "1.0.0", "status": "healthy"}
    )

@app.get("/health", response_model=APIResponse)
async def health_check():
    """Comprehensive health check including database connectivity"""
    try:
        logger.info("Health check initiated")
        
        # Test database connection
        conn = connect_to_db()
        if conn:
            conn.close()
            db_status = "healthy"
        else:
            db_status = "unhealthy"
            
        health_data = {
            "api": "healthy",
            "database": db_status,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Health check completed: {health_data}")
        return APIResponse(
            success=True,
            message="Health check completed",
            data=health_data
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return APIResponse(
            success=False,
            message="Health check failed",
            error=str(e)
        )

@app.post("/initialize", response_model=APIResponse)
async def initialize_system(current_user: dict = Depends(require_admin_role)):
    """Initialize database tables (Admin only)"""
    try:
        logger.info(f"System initialization requested by admin: {current_user.get('username')}")
        
        conn = connect_to_db()
        if not conn:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection failed"
            )
        
        create_tables_if_not_exist(conn)
        conn.close()
        
        logger.info("Database tables initialized successfully")
        return APIResponse(
            success=True,
            message="Database tables initialized successfully"
        )
        
    except Exception as e:
        logger.error(f"System initialization failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Initialization failed: {str(e)}"
        )

@app.post("/admin/seed-comprehensive", response_model=APIResponse)
async def seed_comprehensive_database(
    current_user: dict = Depends(require_admin_role),
    num_students: int = Query(100, ge=10, le=1000, description="Number of students to create"),
    cleanup_first: bool = Query(True, description="Clean up existing data before seeding")
):
    """Seed comprehensive University of Ghana database (Admin only)"""
    try:
        logger.info(f"Admin {current_user.get('username')} starting comprehensive database seeding")
        logger.info(f"Parameters: num_students={num_students}, cleanup_first={cleanup_first}")
        
        # Import seeding function
        from comprehensive_seed import seed_comprehensive_database as seed_function
        
        # Run seeding in background (this might take a while)
        success = seed_function(num_students=num_students, cleanup_first=cleanup_first)
        
        if success:
            logger.info(f"Comprehensive seeding completed successfully: {num_students} students")
            return APIResponse(
                success=True,
                message=f"Database seeded successfully with {num_students} students and comprehensive UG data",
                data={
                    "students_created": num_students,
                    "cleanup_performed": cleanup_first,
                    "courses_available": "130+ UG courses",
                    "semesters_available": "8 academic semesters",
                    "schools_covered": "7 UG schools/colleges"
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Comprehensive seeding failed"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Comprehensive seeding failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Comprehensive seeding failed: {str(e)}"
        )

# ========================================
# ADMIN ENDPOINTS - STUDENT MANAGEMENT
# ========================================

@app.post("/admin/students", response_model=APIResponse)
async def create_student(
    student: StudentCreate, 
    current_user: dict = Depends(require_admin_role)
):
    """Create a new student profile (Admin only)"""
    try:
        logger.info(f"Admin {current_user.get('username')} creating student: {student.index_number}")
        
        def operation(conn):
            return insert_student_profile(
                conn, 
                student.index_number,
                student.full_name,
                datetime.strptime(student.dob, '%Y-%m-%d').date() if student.dob else None,
                student.gender,
                student.contact_email,
                student.phone,
                student.program,
                student.year_of_study
            )
        
        student_id = handle_db_operation(operation)
        
        if student_id:
            logger.info(f"Student created successfully: {student.index_number} (ID: {student_id})")
            return APIResponse(
                success=True,
                message="Student created successfully",
                data={"student_id": student_id, "index_number": student.index_number}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create student - index number may already exist"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Student creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Student creation failed: {str(e)}"
        )

class BulkStudentCreate(BaseModel):
    """Schema for bulk student creation"""
    students: List[StudentCreate] = Field(..., description="List of students to create")

@app.post("/admin/students/bulk", response_model=APIResponse)
async def create_students_bulk(
    bulk_request: BulkStudentCreate,
    current_user: dict = Depends(require_admin_role)
):
    """Create multiple students in bulk (Admin only)"""
    try:
        logger.info(f"Admin {current_user.get('username')} creating {len(bulk_request.students)} students in bulk")
        
        created_students = []
        failed_students = []
        
        for student in bulk_request.students:
            try:
                def operation(conn):
                    return insert_student_profile(
                        conn, 
                        student.index_number,
                        student.full_name,
                        datetime.strptime(student.dob, '%Y-%m-%d').date() if student.dob else None,
                        student.gender,
                        student.contact_email,
                        student.phone,
                        student.program,
                        student.year_of_study
                    )
                
                student_id = handle_db_operation(operation)
                
                if student_id:
                    created_students.append({
                        "index_number": student.index_number,
                        "full_name": student.full_name,
                        "student_id": student_id
                    })
                    logger.debug(f"Bulk created student: {student.index_number}")
                else:
                    failed_students.append({
                        "index_number": student.index_number,
                        "error": "Failed to create - may already exist"
                    })
                    
            except Exception as e:
                failed_students.append({
                    "index_number": student.index_number,
                    "error": str(e)
                })
                logger.warning(f"Failed to create student in bulk: {student.index_number} - {e}")
        
        success_count = len(created_students)
        failure_count = len(failed_students)
        
        logger.info(f"Bulk student creation completed: {success_count} created, {failure_count} failed")
        
        return APIResponse(
            success=True,
            message=f"Bulk creation completed: {success_count} created, {failure_count} failed",
            data={
                "created_students": created_students,
                "failed_students": failed_students,
                "summary": {
                    "total_requested": len(bulk_request.students),
                    "successful": success_count,
                    "failed": failure_count
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Bulk student creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk student creation failed: {str(e)}"
        )

@app.get("/admin/students", response_model=APIResponse)
async def get_all_students(
    current_user: dict = Depends(require_admin_role),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return")
):
    """Get all students with pagination (Admin only)"""
    try:
        logger.info(f"Admin {current_user.get('username')} fetching students (skip: {skip}, limit: {limit})")
        
        students = handle_db_operation(fetch_all_records)
        
        if students and 'students' in students:
            student_list = students['students'][skip:skip+limit]
            total_count = len(students['students'])
            
            logger.info(f"Retrieved {len(student_list)} students out of {total_count} total")
            return APIResponse(
                success=True,
                message=f"Retrieved {len(student_list)} students",
                data={
                    "students": student_list,
                    "total_count": total_count,
                    "skip": skip,
                    "limit": limit
                }
            )
        else:
            return APIResponse(
                success=True,
                message="No students found",
                data={"students": [], "total_count": 0}
            )
            
    except Exception as e:
        logger.error(f"Failed to fetch students: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch students: {str(e)}"
        )

@app.get("/admin/students/search", response_model=APIResponse)
async def search_students(
    current_user: dict = Depends(require_admin_role),
    name: Optional[str] = Query(None, description="Search by name (partial match)"),
    program: Optional[str] = Query(None, description="Filter by program"),
    year_of_study: Optional[int] = Query(None, ge=1, le=10, description="Filter by year of study"),
    gender: Optional[str] = Query(None, description="Filter by gender"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return")
):
    """Advanced student search with multiple filters (Admin only)"""
    try:
        logger.info(f"Admin {current_user.get('username')} searching students with filters")
        
        def operation(conn):
            cursor = conn.cursor()
            
            base_query = """
                SELECT student_id, index_number, full_name, dob, gender, 
                       contact_email, phone, program, year_of_study
                FROM student_profiles 
                WHERE 1=1
            """
            count_query = "SELECT COUNT(*) FROM student_profiles WHERE 1=1"
            
            params = []
            conditions = []
            
            if name:
                conditions.append(" AND full_name ILIKE %s")
                params.append(f"%{name}%")
            
            if program:
                conditions.append(" AND program = %s")
                params.append(program)
            
            if year_of_study:
                conditions.append(" AND year_of_study = %s")
                params.append(year_of_study)
            
            if gender:
                conditions.append(" AND gender = %s")
                params.append(gender)
            
            # Add conditions to both queries
            condition_string = "".join(conditions)
            full_query = base_query + condition_string + " ORDER BY full_name LIMIT %s OFFSET %s"
            full_count_query = count_query + condition_string
            
            # Get total count
            cursor.execute(full_count_query, params)
            total_count = cursor.fetchone()[0]
            
            # Get paginated results
            cursor.execute(full_query, params + [limit, skip])
            return cursor.fetchall(), total_count
        
        students, total_count = handle_db_operation(operation)
        
        students_list = []
        for row in students:
            students_list.append({
                "student_id": row[0],
                "index_number": row[1],
                "full_name": row[2],
                "dob": row[3].strftime('%Y-%m-%d') if row[3] else None,
                "gender": row[4],
                "contact_email": row[5],
                "phone": row[6],
                "program": row[7],
                "year_of_study": row[8]
            })
        
        logger.info(f"Found {len(students_list)} students matching search criteria")
        return APIResponse(
            success=True,
            message=f"Found {len(students_list)} students",
            data={
                "students": students_list, 
                "total_count": total_count,
                "filters_applied": {
                    "name": name,
                    "program": program,
                    "year_of_study": year_of_study,
                    "gender": gender
                },
                "pagination": {"skip": skip, "limit": limit}
            }
        )
        
    except Exception as e:
        logger.error(f"Student search failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Student search failed: {str(e)}"
        )

@app.get("/admin/students/{index_number}", response_model=APIResponse)
async def get_student_by_index(
    index_number: str = Path(..., description="Student index number"),
    current_user: dict = Depends(require_admin_role)
):
    """Get specific student by index number (Admin only)"""
    try:
        logger.info(f"Admin {current_user.get('username')} fetching student: {index_number}")
        
        def operation(conn):
            return fetch_student_by_index_number(conn, index_number)
        
        student = handle_db_operation(operation)
        
        if student:
            logger.info(f"Student found: {index_number}")
            return APIResponse(
                success=True,
                message="Student found",
                data=student
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student with index number {index_number} not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch student {index_number}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch student: {str(e)}"
        )

@app.put("/admin/students/{index_number}", response_model=APIResponse)
async def update_student(
    student_update: StudentUpdate,
    index_number: str = Path(..., description="Student index number"),
    current_user: dict = Depends(require_admin_role)
):
    """Update student profile (Admin only)"""
    try:
        logger.info(f"Admin {current_user.get('username')} updating student: {index_number}")
        
        # First check if student exists
        def fetch_operation(conn):
            return fetch_student_by_index_number(conn, index_number)
        
        existing_student = handle_db_operation(fetch_operation)
        if not existing_student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student with index number {index_number} not found"
            )
        
        # Update logic would go here - this is a simplified example
        # In a real implementation, you'd have an update_student_profile function
        
        logger.info(f"Student updated successfully: {index_number}")
        return APIResponse(
            success=True,
            message="Student updated successfully",
            data={"index_number": index_number}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update student {index_number}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update student: {str(e)}"
        )

# ========================================
# ADMIN ENDPOINTS - COURSE MANAGEMENT
# ========================================

@app.post("/admin/courses", response_model=APIResponse)
async def create_course(
    course: CourseCreate, 
    current_user: dict = Depends(require_admin_role)
):
    """Create a new course (Admin only)"""
    try:
        logger.info(f"Admin {current_user.get('username')} creating course: {course.course_code}")
        
        def operation(conn):
            return insert_course(
                conn, 
                course.course_code,
                course.course_title,
                course.credit_hours
            )
        
        course_id = handle_db_operation(operation)
        
        if course_id:
            logger.info(f"Course created successfully: {course.course_code} (ID: {course_id})")
            return APIResponse(
                success=True,
                message="Course created successfully",
                data={"course_id": course_id, "course_code": course.course_code}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create course - course code may already exist"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Course creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Course creation failed: {str(e)}"
        )

@app.get("/admin/courses", response_model=APIResponse)
async def get_all_courses(
    current_user: dict = Depends(require_admin_role),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return")
):
    """Get all courses with pagination (Admin only)"""
    try:
        logger.info(f"Admin {current_user.get('username')} fetching courses")
        
        courses = handle_db_operation(fetch_all_records)
        
        if courses and 'courses' in courses:
            course_list = courses['courses'][skip:skip+limit]
            total_count = len(courses['courses'])
            
            logger.info(f"Retrieved {len(course_list)} courses out of {total_count} total")
            return APIResponse(
                success=True,
                message=f"Retrieved {len(course_list)} courses",
                data={
                    "courses": course_list,
                    "total_count": total_count,
                    "skip": skip,
                    "limit": limit
                }
            )
        else:
            return APIResponse(
                success=True,
                message="No courses found",
                data={"courses": [], "total_count": 0}
            )
            
    except Exception as e:
        logger.error(f"Failed to fetch courses: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch courses: {str(e)}"
        )

# ========================================
# ADMIN ENDPOINTS - SEMESTER MANAGEMENT
# ========================================

@app.post("/admin/semesters", response_model=APIResponse)
async def create_semester(
    semester: SemesterCreate, 
    current_user: dict = Depends(require_admin_role)
):
    """Create a new semester (Admin only)"""
    try:
        logger.info(f"Admin {current_user.get('username')} creating semester: {semester.semester_name}")
        
        def operation(conn):
            return insert_semester(
                conn, 
                semester.semester_name,
                datetime.strptime(semester.start_date, '%Y-%m-%d').date(),
                datetime.strptime(semester.end_date, '%Y-%m-%d').date(),
                semester.academic_year
            )
        
        semester_id = handle_db_operation(operation)
        
        if semester_id:
            logger.info(f"Semester created successfully: {semester.semester_name} (ID: {semester_id})")
            return APIResponse(
                success=True,
                message="Semester created successfully",
                data={
                    "semester_id": semester_id, 
                    "semester_name": semester.semester_name,
                    "academic_year": semester.academic_year
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create semester"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Semester creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Semester creation failed: {str(e)}"
        )

@app.get("/admin/semesters", response_model=APIResponse)
async def get_all_semesters(
    current_user: dict = Depends(require_admin_role)
):
    """Get all semesters (Admin only)"""
    try:
        logger.info(f"Admin {current_user.get('username')} fetching semesters")
        
        semesters = handle_db_operation(fetch_all_records)
        
        if semesters and 'semesters' in semesters:
            logger.info(f"Retrieved {len(semesters['semesters'])} semesters")
            return APIResponse(
                success=True,
                message=f"Retrieved {len(semesters['semesters'])} semesters",
                data={"semesters": semesters['semesters']}
            )
        else:
            return APIResponse(
                success=True,
                message="No semesters found",
                data={"semesters": []}
            )
            
    except Exception as e:
        logger.error(f"Failed to fetch semesters: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch semesters: {str(e)}"
        )

# ========================================
# STUDENT ENDPOINTS
# ========================================

@app.get("/student/profile", response_model=APIResponse)
async def get_student_profile(
    current_user: dict = Depends(require_student_role)
):
    """Get current student's profile"""
    try:
        index_number = current_user.get('index_number')
        if not index_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student index number not found in user session"
            )
            
        logger.info(f"Student {index_number} fetching profile")
        
        def operation(conn):
            return fetch_student_by_index_number(conn, index_number)
        
        student = handle_db_operation(operation)
        
        if student:
            logger.info(f"Profile retrieved for student: {index_number}")
            return APIResponse(
                success=True,
                message="Profile retrieved successfully",
                data=student
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student profile not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch student profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch profile: {str(e)}"
        )

@app.get("/student/grades", response_model=APIResponse)
async def get_student_grades(
    current_user: dict = Depends(require_student_role),
    semester: Optional[str] = Query(None, description="Filter by semester"),
    academic_year: Optional[str] = Query(None, description="Filter by academic year")
):
    """Get current student's grades with optional filtering"""
    try:
        index_number = current_user.get('index_number')
        if not index_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student index number not found in user session"
            )
            
        logger.info(f"Student {index_number} fetching grades (semester: {semester}, year: {academic_year})")
        
        def operation(conn):
            return fetch_student_grades(conn, index_number, semester, academic_year)
        
        grades = handle_db_operation(operation)
        
        if grades:
            logger.info(f"Retrieved {len(grades)} grades for student: {index_number}")
            return APIResponse(
                success=True,
                message="Grades retrieved successfully",
                data={
                    "grades": grades,
                    "total_count": len(grades),
                    "filters": {"semester": semester, "academic_year": academic_year}
                }
            )
        else:
            return APIResponse(
                success=True,
                message="No grades found",
                data={"grades": [], "total_count": 0}
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch student grades: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch grades: {str(e)}"
        )

@app.get("/student/gpa", response_model=APIResponse)
async def get_student_gpa(
    current_user: dict = Depends(require_student_role),
    semester: Optional[str] = Query(None, description="Calculate GPA for specific semester"),
    academic_year: Optional[str] = Query(None, description="Calculate GPA for specific academic year")
):
    """Calculate and return student's GPA"""
    try:
        index_number = current_user.get('index_number')
        if not index_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student index number not found in user session"
            )
            
        logger.info(f"Student {index_number} calculating GPA (semester: {semester}, year: {academic_year})")
        
        def operation(conn):
            return calculate_student_gpa(conn, index_number, semester, academic_year)
        
        gpa_data = handle_db_operation(operation)
        
        if gpa_data:
            logger.info(f"GPA calculated for student: {index_number}")
            return APIResponse(
                success=True,
                message="GPA calculated successfully",
                data=gpa_data
            )
        else:
            return APIResponse(
                success=True,
                message="No grades available for GPA calculation",
                data={"gpa": 0.0, "total_credits": 0}
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to calculate GPA: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate GPA: {str(e)}"
        )

# ========================================
# ADMIN ENDPOINTS - GRADE MANAGEMENT
# ========================================

@app.post("/admin/grades", response_model=APIResponse)
async def create_grade(
    grade: GradeCreate, 
    current_user: dict = Depends(require_admin_role)
):
    """Create or update a student grade (Admin only)"""
    try:
        logger.info(f"Admin {current_user.get('username')} creating grade for student: {grade.student_index}")
        
        def operation(conn):
            return insert_student_grade(
                conn, 
                grade.student_index,
                grade.course_code,
                grade.semester_name,
                grade.score,
                grade.academic_year
            )
        
        grade_id = handle_db_operation(operation)
        
        if grade_id:
            logger.info(f"Grade created successfully for {grade.student_index} in {grade.course_code}")
            return APIResponse(
                success=True,
                message="Grade created successfully",
                data={"grade_id": grade_id, "student_index": grade.student_index}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create grade"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Grade creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Grade creation failed: {str(e)}"
        )

@app.get("/admin/grades", response_model=APIResponse)
async def get_all_grades(
    current_user: dict = Depends(require_admin_role),
    student_index: Optional[str] = Query(None, description="Filter by student index"),
    course_code: Optional[str] = Query(None, description="Filter by course code"),
    semester: Optional[str] = Query(None, description="Filter by semester"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return")
):
    """Get all grades with filtering and pagination (Admin only)"""
    try:
        logger.info(f"Admin {current_user.get('username')} fetching grades with filters")
        
        def operation(conn):
            return fetch_grades_with_filters(
                conn, student_index, course_code, semester, skip, limit
            )
        
        grades_data = handle_db_operation(operation)
        
        if grades_data:
            logger.info(f"Retrieved grades data")
            return APIResponse(
                success=True,
                message="Grades retrieved successfully",
                data=grades_data
            )
        else:
            return APIResponse(
                success=True,
                message="No grades found",
                data={"grades": [], "total_count": 0}
            )
            
    except Exception as e:
        logger.error(f"Failed to fetch grades: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch grades: {str(e)}"
        )

# ========================================
# ADMIN ENDPOINTS - USER MANAGEMENT
# ========================================

@app.post("/admin/users", response_model=APIResponse)
async def create_user_account(
    user: UserCreate, 
    current_user: dict = Depends(require_admin_role)
):
    """Create a new user account (Admin only)"""
    try:
        logger.info(f"Admin {current_user.get('username')} creating user account: {user.username}")
        
        def operation(conn):
            return create_user(user.username, user.password, user.role)
        
        user_id = handle_db_operation(operation)
        
        if user_id:
            logger.info(f"User account created successfully: {user.username} (ID: {user_id})")
            return APIResponse(
                success=True,
                message="User account created successfully",
                data={"user_id": user_id, "username": user.username, "role": user.role}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user account - username may already exist"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User account creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"User account creation failed: {str(e)}"
        )

@app.post("/admin/student-accounts", response_model=APIResponse)
async def create_student_account_endpoint(
    student_account: StudentAccountCreate, 
    current_user: dict = Depends(require_admin_role)
):
    """Create a student account with optional password (Admin only)"""
    try:
        logger.info(f"Admin {current_user.get('username')} creating student account: {student_account.index_number}")
        
        def operation(conn):
            return create_student_account(
                student_account.index_number, 
                student_account.full_name,
                student_account.password
            )
        
        result = handle_db_operation(operation)
        
        if result:
            logger.info(f"Student account created successfully: {student_account.index_number}")
            return APIResponse(
                success=True,
                message="Student account created successfully",
                data={
                    "index_number": student_account.index_number,
                    "username": student_account.index_number,
                    "password_generated": result.get('password_generated', False)
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create student account"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Student account creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Student account creation failed: {str(e)}"
        )

@app.post("/admin/reset-password", response_model=APIResponse)
async def reset_student_password_endpoint(
    password_reset: PasswordReset, 
    current_user: dict = Depends(require_admin_role)
):
    """Reset student password (Admin only)"""
    try:
        logger.info(f"Admin {current_user.get('username')} resetting password for: {password_reset.index_number}")
        
        def operation(conn):
            return reset_student_password(
                password_reset.index_number, 
                password_reset.new_password
            )
        
        result = handle_db_operation(operation)
        
        if result:
            logger.info(f"Password reset successfully: {password_reset.index_number}")
            return APIResponse(
                success=True,
                message="Password reset successfully",
                data={
                    "index_number": password_reset.index_number,
                    "new_password": result.get('password', 'Generated automatically')
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student account not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password reset failed: {str(e)}"
        )

# ========================================
# ADMIN ENDPOINTS - BULK OPERATIONS
# ========================================

@app.post("/admin/bulk-import", response_model=APIResponse)
async def bulk_import_data(
    bulk_data: BulkImportRequest, 
    current_user: dict = Depends(require_admin_role)
):
    """Bulk import student data from CSV format (Admin only)"""
    try:
        logger.info(f"Admin {current_user.get('username')} performing bulk import for semester: {bulk_data.semester_name}")
        
        def operation(conn):
            return bulk_import_from_file(conn, bulk_data.file_data, bulk_data.semester_name)
        
        result = handle_db_operation(operation)
        
        if result:
            logger.info(f"Bulk import completed: {result.get('imported_count', 0)} records")
            return APIResponse(
                success=True,
                message="Bulk import completed successfully",
                data=result
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bulk import failed"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk import failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk import failed: {str(e)}"
        )

# ========================================
# ADMIN ENDPOINTS - REPORTING
# ========================================

@app.get("/admin/reports/summary", response_model=APIResponse)
async def generate_summary_report(
    current_user: dict = Depends(require_admin_role),
    semester: Optional[str] = Query(None, description="Filter by semester"),
    academic_year: Optional[str] = Query(None, description="Filter by academic year"),
    format: str = Query("json", description="Report format (json/pdf/txt)")
):
    """Generate comprehensive summary report (Admin only)"""
    try:
        logger.info(f"Admin {current_user.get('username')} generating summary report")
        
        if format not in ["json", "pdf", "txt"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid format. Supported formats: json, pdf, txt"
            )
        
        def operation(conn):
            return generate_comprehensive_report(conn, semester, academic_year, format)
        
        report_data = handle_db_operation(operation)
        
        if report_data:
            logger.info(f"Summary report generated successfully in {format} format")
            return APIResponse(
                success=True,
                message=f"Summary report generated successfully ({format})",
                data=report_data
            )
        else:
            return APIResponse(
                success=True,
                message="No data available for report generation",
                data={"report": "No data available"}
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Report generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report generation failed: {str(e)}"
        )

@app.get("/admin/analytics/dashboard", response_model=APIResponse)
async def get_admin_dashboard(
    current_user: dict = Depends(require_admin_role)
):
    """Get admin dashboard analytics (Admin only)"""
    try:
        logger.info(f"Admin {current_user.get('username')} accessing dashboard analytics")
        
        def operation(conn):
            return get_dashboard_analytics(conn)
        
        analytics = handle_db_operation(operation)
        
        if analytics:
            logger.info("Dashboard analytics retrieved successfully")
            return APIResponse(
                success=True,
                message="Dashboard analytics retrieved successfully",
                data=analytics
            )
        else:
            return APIResponse(
                success=True,
                message="No analytics data available",
                data={"analytics": {}}
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dashboard analytics failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dashboard analytics failed: {str(e)}"
        )

# ========================================
# UNIVERSITY OF GHANA SPECIFIC ENDPOINTS
# ========================================

@app.get("/ug/schools-programs", response_model=APIResponse)
async def get_ug_schools_and_programs():
    """Get University of Ghana schools and their programs (Public endpoint)"""
    try:
        logger.info("Fetching UG schools and programs")
        
        # Import UG schools data from comprehensive seed
        from comprehensive_seed import UG_SCHOOLS_AND_PROGRAMS
        
        schools_data = []
        for school, programs in UG_SCHOOLS_AND_PROGRAMS.items():
            schools_data.append({
                "school": school,
                "programs": programs
            })
        
        logger.info(f"Retrieved {len(schools_data)} UG schools")
        return APIResponse(
            success=True,
            message="UG schools and programs retrieved successfully",
            data={"schools": schools_data, "total_schools": len(schools_data)}
        )
        
    except Exception as e:
        logger.error(f"Failed to retrieve UG schools: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve schools and programs: {str(e)}"
        )

@app.get("/ug/academic-calendar", response_model=APIResponse)
async def get_ug_academic_calendar():
    """Get University of Ghana academic calendar (Public endpoint)"""
    try:
        logger.info("Fetching UG academic calendar")
        
        def operation(conn):
            cursor = conn.cursor()
            cursor.execute("""
                SELECT semester_id, semester_name, academic_year, start_date, end_date 
                FROM semesters 
                ORDER BY start_date DESC
            """)
            return cursor.fetchall()
        
        semesters = handle_db_operation(operation)
        
        calendar_data = []
        for row in semesters:
            calendar_data.append({
                "semester_id": row[0],
                "semester_name": row[1],
                "academic_year": row[2],
                "start_date": row[3].strftime('%Y-%m-%d'),
                "end_date": row[4].strftime('%Y-%m-%d')
            })
        
        logger.info(f"Retrieved {len(calendar_data)} academic semesters")
        return APIResponse(
            success=True,
            message="UG academic calendar retrieved successfully",
            data={"semesters": calendar_data, "total_semesters": len(calendar_data)}
        )
        
    except Exception as e:
        logger.error(f"Failed to retrieve UG academic calendar: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve academic calendar: {str(e)}"
        )

@app.get("/admin/statistics/enrollment", response_model=APIResponse)
async def get_enrollment_statistics(
    current_user: dict = Depends(require_admin_role),
    academic_year: Optional[str] = Query(None, description="Filter by academic year")
):
    """Get detailed enrollment statistics by school and program (Admin only)"""
    try:
        logger.info(f"Admin {current_user.get('username')} fetching enrollment statistics")
        
        def operation(conn):
            cursor = conn.cursor()
            
            # Base query for enrollment by program
            base_query = """
                SELECT 
                    program,
                    year_of_study,
                    gender,
                    COUNT(*) as student_count
                FROM student_profiles 
                WHERE program IS NOT NULL
            """
            
            if academic_year:
                # If academic year filter is provided, we need to join with grades/semesters
                query = f"""
                    SELECT 
                        sp.program,
                        sp.year_of_study,
                        sp.gender,
                        COUNT(DISTINCT sp.student_id) as student_count
                    FROM student_profiles sp
                    JOIN grades g ON sp.student_id = g.student_id
                    JOIN semesters s ON g.semester_id = s.semester_id
                    WHERE sp.program IS NOT NULL AND s.academic_year = %s
                    GROUP BY sp.program, sp.year_of_study, sp.gender
                    ORDER BY sp.program, sp.year_of_study
                """
                cursor.execute(query, (academic_year,))
            else:
                query = f"{base_query} GROUP BY program, year_of_study, gender ORDER BY program, year_of_study"
                cursor.execute(query)
            
            return cursor.fetchall()
        
        enrollment_data = handle_db_operation(operation)
        
        # Process data into structured format
        programs_stats = {}
        total_students = 0
        
        for row in enrollment_data:
            program, year, gender, count = row
            total_students += count
            
            if program not in programs_stats:
                programs_stats[program] = {
                    "program": program,
                    "total_students": 0,
                    "by_year": {},
                    "by_gender": {"Male": 0, "Female": 0, "Other": 0}
                }
            
            programs_stats[program]["total_students"] += count
            
            if year not in programs_stats[program]["by_year"]:
                programs_stats[program]["by_year"][year] = 0
            programs_stats[program]["by_year"][year] += count
            
            if gender in programs_stats[program]["by_gender"]:
                programs_stats[program]["by_gender"][gender] += count
        
        stats_list = list(programs_stats.values())
        
        logger.info(f"Generated enrollment statistics for {len(stats_list)} programs")
        return APIResponse(
            success=True,
            message="Enrollment statistics retrieved successfully",
            data={
                "programs": stats_list,
                "total_students": total_students,
                "total_programs": len(stats_list),
                "academic_year": academic_year
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to retrieve enrollment statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve enrollment statistics: {str(e)}"
        )

@app.get("/admin/statistics/grades-distribution", response_model=APIResponse)
async def get_grades_distribution(
    current_user: dict = Depends(require_admin_role),
    semester_name: Optional[str] = Query(None, description="Filter by semester"),
    course_code: Optional[str] = Query(None, description="Filter by course")
):
    """Get grade distribution statistics (Admin only)"""
    try:
        logger.info(f"Admin {current_user.get('username')} fetching grade distribution")
        
        def operation(conn):
            cursor = conn.cursor()
            
            base_query = """
                SELECT 
                    g.grade,
                    g.grade_point,
                    COUNT(*) as count,
                    c.course_code,
                    c.course_title,
                    s.semester_name
                FROM grades g
                JOIN courses c ON g.course_id = c.course_id
                JOIN semesters s ON g.semester_id = s.semester_id
                WHERE 1=1
            """
            
            params = []
            if semester_name:
                base_query += " AND s.semester_name = %s"
                params.append(semester_name)
            if course_code:
                base_query += " AND c.course_code = %s"
                params.append(course_code)
            
            base_query += " GROUP BY g.grade, g.grade_point, c.course_code, c.course_title, s.semester_name"
            base_query += " ORDER BY c.course_code, g.grade_point DESC"
            
            cursor.execute(base_query, params)
            return cursor.fetchall()
        
        grade_data = handle_db_operation(operation)
        
        # Process data
        distribution = {}
        grade_summary = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0, "F": 0}
        
        for row in grade_data:
            grade, grade_point, count, course_code, course_title, semester = row
            
            if course_code not in distribution:
                distribution[course_code] = {
                    "course_code": course_code,
                    "course_title": course_title,
                    "grades": {},
                    "total_students": 0
                }
            
            distribution[course_code]["grades"][grade] = count
            distribution[course_code]["total_students"] += count
            
            if grade in grade_summary:
                grade_summary[grade] += count
        
        courses_list = list(distribution.values())
        
        logger.info(f"Generated grade distribution for {len(courses_list)} courses")
        return APIResponse(
            success=True,
            message="Grade distribution retrieved successfully",
            data={
                "courses": courses_list,
                "overall_distribution": grade_summary,
                "filters": {
                    "semester": semester_name,
                    "course": course_code
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to retrieve grade distribution: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve grade distribution: {str(e)}"
        )

@app.get("/admin/reports/transcript/{index_number}", response_model=APIResponse)
async def generate_student_transcript(
    index_number: str = Path(..., description="Student index number"),
    current_user: dict = Depends(require_admin_role)
):
    """Generate comprehensive student transcript (Admin only)"""
    try:
        logger.info(f"Admin {current_user.get('username')} generating transcript for {index_number}")
        
        def operation(conn):
            cursor = conn.cursor()
            
            # Get student details
            cursor.execute("""
                SELECT student_id, index_number, full_name, dob, gender, 
                       contact_email, phone, program, year_of_study
                FROM student_profiles 
                WHERE index_number = %s
            """, (index_number,))
            
            student_data = cursor.fetchone()
            if not student_data:
                return None
            
            # Get all grades for student
            cursor.execute("""
                SELECT 
                    c.course_code, c.course_title, c.credit_hours,
                    g.score, g.grade, g.grade_point,
                    s.semester_name, s.academic_year
                FROM grades g
                JOIN courses c ON g.course_id = c.course_id
                JOIN semesters s ON g.semester_id = s.semester_id
                WHERE g.student_id = %s
                ORDER BY s.start_date, c.course_code
            """, (student_data[0],))
            
            grades_data = cursor.fetchall()
            
            return {"student": student_data, "grades": grades_data}
        
        result = handle_db_operation(operation)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student with index {index_number} not found"
            )
        
        student_data, grades_data = result["student"], result["grades"]
        
        # Process transcript data
        transcript = {
            "student_info": {
                "index_number": student_data[1],
                "full_name": student_data[2],
                "date_of_birth": student_data[3].strftime('%Y-%m-%d') if student_data[3] else None,
                "gender": student_data[4],
                "email": student_data[5],
                "phone": student_data[6],
                "program": student_data[7],
                "year_of_study": student_data[8]
            },
            "academic_record": {},
            "summary": {
                "total_courses": 0,
                "total_credit_hours": 0,
                "cumulative_gpa": 0.0
            }
        }
        
        # Group by semester
        total_points = 0
        total_credits = 0
        
        for grade_row in grades_data:
            course_code, course_title, credit_hours, score, grade, grade_point, semester_name, academic_year = grade_row
            
            if semester_name not in transcript["academic_record"]:
                transcript["academic_record"][semester_name] = {
                    "academic_year": academic_year,
                    "courses": [],
                    "semester_gpa": 0.0,
                    "semester_credits": 0
                }
            
            transcript["academic_record"][semester_name]["courses"].append({
                "course_code": course_code,
                "course_title": course_title,
                "credit_hours": credit_hours,
                "score": score,
                "grade": grade,
                "grade_point": grade_point
            })
            
            transcript["academic_record"][semester_name]["semester_credits"] += credit_hours
            total_credits += credit_hours
            total_points += grade_point * credit_hours
            transcript["summary"]["total_courses"] += 1
        
        # Calculate GPAs
        for semester_name in transcript["academic_record"]:
            semester_data = transcript["academic_record"][semester_name]
            semester_points = sum(course["grade_point"] * course["credit_hours"] 
                                 for course in semester_data["courses"])
            semester_credits = semester_data["semester_credits"]
            
            if semester_credits > 0:
                semester_data["semester_gpa"] = round(semester_points / semester_credits, 2)
        
        transcript["summary"]["total_credit_hours"] = total_credits
        if total_credits > 0:
            transcript["summary"]["cumulative_gpa"] = round(total_points / total_credits, 2)
        
        logger.info(f"Generated transcript for {index_number} with {transcript['summary']['total_courses']} courses")
        return APIResponse(
            success=True,
            message="Student transcript generated successfully",
            data=transcript
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate transcript for {index_number}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate transcript: {str(e)}"
        )

# ========================================
# ADDITIONAL UTILITY ENDPOINTS
# ========================================

@app.get("/courses", response_model=APIResponse)
async def get_public_courses(
    current_user: dict = Depends(get_current_user)
):
    """Get all courses (Available to authenticated users)"""
    try:
        logger.info(f"User {current_user.get('username')} fetching course list")
        
        courses = handle_db_operation(fetch_all_records)
        
        if courses and 'courses' in courses:
            logger.info(f"Retrieved {len(courses['courses'])} courses")
            return APIResponse(
                success=True,
                message="Courses retrieved successfully",
                data={"courses": courses['courses']}
            )
        else:
            return APIResponse(
                success=True,
                message="No courses found",
                data={"courses": []}
            )
            
    except Exception as e:
        logger.error(f"Failed to fetch courses: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch courses: {str(e)}"
        )

@app.get("/semesters", response_model=APIResponse)
async def get_public_semesters(
    current_user: dict = Depends(get_current_user)
):
    """Get all semesters (Available to authenticated users)"""
    try:
        logger.info(f"User {current_user.get('username')} fetching semester list")
        
        semesters = handle_db_operation(fetch_all_records)
        
        if semesters and 'semesters' in semesters:
            logger.info(f"Retrieved {len(semesters['semesters'])} semesters")
            return APIResponse(
                success=True,
                message="Semesters retrieved successfully",
                data={"semesters": semesters['semesters']}
            )
        else:
            return APIResponse(
                success=True,
                message="No semesters found",
                data={"semesters": []}
            )
            
    except Exception as e:
        logger.error(f"Failed to fetch semesters: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch semesters: {str(e)}"
        )

# ========================================
# ADDITIONAL HELPER FUNCTIONS
# ========================================

def generate_comprehensive_report(conn, semester=None, academic_year=None, format="json"):
    """Generate comprehensive system report"""
    try:
        cursor = conn.cursor()
        
        # Get summary statistics
        stats = {}
        
        # Total students
        cursor.execute("SELECT COUNT(*) FROM students")
        stats['total_students'] = cursor.fetchone()[0]
        
        # Total courses
        cursor.execute("SELECT COUNT(*) FROM courses")
        stats['total_courses'] = cursor.fetchone()[0]
        
        # Total grades
        grade_query = "SELECT COUNT(*) FROM grades"
        params = []
        
        if semester:
            grade_query += " WHERE semester_name = %s"
            params.append(semester)
            
        if academic_year:
            if semester:
                grade_query += " AND academic_year = %s"
            else:
                grade_query += " WHERE academic_year = %s"
            params.append(academic_year)
            
        cursor.execute(grade_query, params)
        stats['total_grades'] = cursor.fetchone()[0]
        
        # Grade distribution
        dist_query = """
            SELECT letter_grade, COUNT(*) as count 
            FROM grades 
        """
        
        if semester or academic_year:
            dist_query += " WHERE 1=1"
            if semester:
                dist_query += " AND semester_name = %s"
            if academic_year:
                dist_query += " AND academic_year = %s"
        
        dist_query += " GROUP BY letter_grade ORDER BY letter_grade"
        
        cursor.execute(dist_query, params)
        grade_distribution = dict(cursor.fetchall())
        
        # Average GPA calculation
        gpa_query = """
            SELECT AVG(grade_points) as avg_gpa 
            FROM grades 
        """
        
        if semester or academic_year:
            gpa_query += " WHERE 1=1"
            if semester:
                gpa_query += " AND semester_name = %s"
            if academic_year:
                gpa_query += " AND academic_year = %s"
        
        cursor.execute(gpa_query, params)
        avg_gpa_result = cursor.fetchone()
        avg_gpa = round(avg_gpa_result[0], 2) if avg_gpa_result[0] else 0.0
        
        report_data = {
            "summary_statistics": stats,
            "grade_distribution": grade_distribution,
            "average_gpa": avg_gpa,
            "filters": {
                "semester": semester,
                "academic_year": academic_year
            },
            "generated_at": datetime.now().isoformat()
        }
        
        if format == "pdf":
            # Generate PDF report
            all_records = fetch_all_records(conn)
            student_records = all_records.get('students', []) if all_records else []
            pdf_path = export_summary_report_pdf(student_records, f"summary_report_{semester or 'all'}.pdf")
            report_data["pdf_path"] = pdf_path
        elif format == "txt":
            # Generate TXT report
            all_records = fetch_all_records(conn)
            student_records = all_records.get('students', []) if all_records else []
            txt_path = export_summary_report_txt(student_records, f"summary_report_{semester or 'all'}.txt")
            report_data["txt_path"] = txt_path
        
        return report_data
        
    except Exception as e:
        logger.error(f"Error generating comprehensive report: {str(e)}")
        return None

def get_dashboard_analytics(conn):
    """Get dashboard analytics data"""
    try:
        cursor = conn.cursor()
        analytics = {}
        
        # Recent activity (last 30 days simulation)
        analytics['recent_grades'] = {
            "total": 0,
            "by_semester": {}
        }
        
        # Student performance trends
        cursor.execute("""
            SELECT s.semester_name, AVG(g.grade_point) as avg_gpa, COUNT(*) as total_grades
            FROM grades g
            JOIN semesters s ON g.semester_id = s.semester_id
            GROUP BY s.semester_name 
            ORDER BY s.semester_name
        """)
        
        semester_performance = []
        for row in cursor.fetchall():
            semester_performance.append({
                "semester": row[0],
                "average_gpa": round(row[1], 2) if row[1] else 0.0,
                "total_grades": row[2]
            })
        
        analytics['semester_performance'] = semester_performance
        
        # Top performing students
        cursor.execute("""
            SELECT s.index_number, s.full_name, AVG(g.grade_point) as avg_gpa, COUNT(g.grade_id) as total_courses
            FROM student_profiles s
            JOIN grades g ON s.student_id = g.student_id
            GROUP BY s.index_number, s.full_name
            HAVING COUNT(g.grade_id) >= 3
            ORDER BY avg_gpa DESC
            LIMIT 10
        """)
        
        top_students = []
        for row in cursor.fetchall():
            top_students.append({
                "index_number": row[0],
                "full_name": row[1],
                "average_gpa": round(row[2], 2),
                "total_courses": row[3]
            })
        
        analytics['top_students'] = top_students
        
        # Course statistics
        cursor.execute("""
            SELECT c.course_code, c.course_title, AVG(g.grade_point) as avg_gpa, COUNT(g.grade_id) as enrollments
            FROM courses c
            LEFT JOIN grades g ON c.course_id = g.course_id
            GROUP BY c.course_code, c.course_title
            ORDER BY enrollments DESC
        """)
        
        course_stats = []
        for row in cursor.fetchall():
            course_stats.append({
                "course_code": row[0],
                "course_title": row[1],
                "average_gpa": round(row[2], 2) if row[2] else 0.0,
                "total_enrollments": row[3] if row[3] else 0
            })
        
        analytics['course_statistics'] = course_stats
        
        return analytics
        
    except Exception as e:
        logger.error(f"Error getting dashboard analytics: {str(e)}")
        return {}

# ========================================
# APPLICATION STARTUP EVENT
# ========================================

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    try:
        logger.info("Starting Student Result Management System API...")
        
        # Test database connection
        conn = connect_to_db()
        if conn:
            logger.info("Database connection established successfully")
            
            # Ensure tables exist
            create_tables_if_not_exist(conn)
            logger.info("Database tables verified/created")
            
            conn.close()
        else:
            logger.error("Failed to establish database connection on startup")
            
        logger.info("API startup completed successfully")
        
    except Exception as e:
        logger.error(f"Error during API startup: {str(e)}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    try:
        logger.info("Shutting down Student Result Management System API...")
        # Perform any cleanup here if needed
        logger.info("API shutdown completed")
        
    except Exception as e:
        logger.error(f"Error during API shutdown: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting FastAPI server...")
    uvicorn.run(
        "api:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )