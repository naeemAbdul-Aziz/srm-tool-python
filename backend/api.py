# api.py - FastAPI application for Student Result Management System
# Production-ready REST API with comprehensive endpoints, authentication, and error handling

from fastapi import FastAPI, HTTPException, Depends, status, Query, Path, Response, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
import os
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from psycopg2.extras import RealDictCursor
try:  # Prefer package-relative imports
    from .db import (
        connect_to_db, delete_student_profile, fetch_all_records, insert_student_profile, fetch_student_by_index_number,
        insert_course, fetch_all_courses, fetch_course_by_code, insert_semester, fetch_all_semesters, update_course, update_semester, update_student_profile,
        update_student_score, delete_course, delete_semester, insert_grade,
        fetch_semester_by_name, create_tables_if_not_exist,
        insert_notification, _expand_audience_user_ids, create_user_notification_links,
        fetch_user_notifications, mark_notification_read, mark_all_notifications_read, count_unread_notifications,
        fetch_assessments, create_assessment, update_assessment, delete_assessment
    )
    from .grade_util import calculate_grade, get_grade_point, calculate_gpa, summarize_grades
    from .auth import (
        authenticate_user, create_user, create_student_account, reset_student_password
    )
    from .bulk_importer import bulk_import_from_file
    from .report_utils import (
        export_summary_report_pdf,
        export_summary_report_txt,
        export_summary_report_excel,
        export_summary_report_csv,
        export_academic_transcript_excel,
        export_academic_transcript_pdf
    )
    from .logger import get_logger
    from .session import session_manager
except ImportError:  # Fallback for legacy direct execution (e.g. `uvicorn api:app`)
    from db import (
        connect_to_db, delete_student_profile, fetch_all_records, insert_student_profile, fetch_student_by_index_number,
        insert_course, fetch_all_courses, fetch_course_by_code, insert_semester, fetch_all_semesters, update_course, update_semester, update_student_profile,
        update_student_score, delete_course, delete_semester, insert_grade,
        fetch_semester_by_name, create_tables_if_not_exist,
        insert_notification, _expand_audience_user_ids, create_user_notification_links,
        fetch_user_notifications, mark_notification_read, mark_all_notifications_read, count_unread_notifications,
        fetch_assessments, create_assessment, update_assessment, delete_assessment
    )
    from grade_util import calculate_grade, get_grade_point, calculate_gpa, summarize_grades
    from auth import (
        authenticate_user, create_user, create_student_account, reset_student_password
    )
    from bulk_importer import bulk_import_from_file
    from report_utils import (
        export_summary_report_pdf,
        export_summary_report_txt,
        export_summary_report_excel,
        export_summary_report_csv,
        export_academic_transcript_excel,
        export_academic_transcript_pdf
    )
    from logger import get_logger
    from session import session_manager
import traceback

# Initialize logger
logger = get_logger(__name__)

# Initialize FastAPI app with metadata
from contextlib import asynccontextmanager
import asyncio

@asynccontextmanager
async def lifespan(app_instance):
    """Custom lifespan context to perform startup/shutdown while swallowing
    benign asyncio.CancelledError that occurs during uvicorn --reload restarts.
    """
    try:
        logger.info("Starting Student Result Management System API (lifespan)...")
        # Startup tasks (mirrors existing startup_event logic but we keep backward compat by still firing handlers)
        yield
    except asyncio.CancelledError:
        # Suppress noisy stack during reload
        logger.debug("Lifespan cancelled (reload) – suppressing traceback")
        raise
    finally:
        logger.info("Lifespan shutdown sequence executing")

app = FastAPI(
    title="Student Result Management System API",
    description="Comprehensive API for managing student records, grades, and academic reports",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

#! Notification broadcaster moved below auth dependency definitions

# Configure CORS for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Mount static files (frontend)
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

# HTTP Basic Authentication setup
security = HTTPBasic()

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

# =============================
# NOTIFICATION MODELS
# =============================

class NotificationCreate(BaseModel):
    type: str
    title: str
    message: str
    severity: Optional[str] = 'info'
    audience: Optional[str] = 'all'  # all|admins|students|user
    target_user_id: Optional[int] = None
    expires_at: Optional[datetime] = None

class UserNotificationOut(BaseModel):
    user_notification_id: int
    notification_id: int
    type: str
    title: str
    message: str
    severity: str
    audience: str
    is_read: bool
    read_at: Optional[datetime]
    created_at: datetime

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
    grade_id: int # Added grade_id to match db schema
    student_index: str
    student_name: str
    course_code: str
    course_title: str
    semester_name: str
    academic_year: str
    score: float
    grade: str
    grade_point: float

# =============================
# ASSESSMENT MODELS
# =============================

class AssessmentCreate(BaseModel):
    course_code: str = Field(..., description="Course code the assessment belongs to")
    assessment_name: str = Field(..., min_length=1, max_length=100)
    max_score: int = Field(..., ge=1, le=1000)
    weight: float = Field(..., ge=0, le=100, description="Weight percentage contributing to final grade")

class AssessmentUpdate(BaseModel):
    assessment_name: Optional[str] = Field(None, min_length=1, max_length=100)
    max_score: Optional[int] = Field(None, ge=1, le=1000)
    weight: Optional[float] = Field(None, ge=0, le=100)

class AssessmentOut(BaseModel):
    assessment_id: int
    assessment_name: str
    max_score: int
    weight: float
    course_id: int
    course_code: str
    course_title: str

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
        logger.debug(f"[AUTH] Attempt for user: {credentials.username}")
        logger.debug(f"[AUTH] Raw credentials: username={credentials.username}, password={'*' * len(credentials.password) if credentials.password else ''}")
        user = authenticate_user(credentials.username, credentials.password)
        if not user:
            logger.warning(f"[AUTH] Authentication failed for user: {credentials.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Basic"},
            )
        logger.info(f"[AUTH] User authenticated successfully: {credentials.username} ({user.get('role')})")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[AUTH] Authentication error for user {credentials.username}: {str(e)}")
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

# =====================================================
# SIMPLE IN-PROCESS SSE BROADCASTER FOR NOTIFICATIONS (after auth deps)
# =====================================================
import json, time
from typing import Set

class NotificationBroadcaster:
    """Minimal async pub/sub for server-sent notification events."""
    def __init__(self):
        self._listeners: Set[asyncio.Queue] = set()
        self._lock = asyncio.Lock()

    async def register(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        async with self._lock:
            self._listeners.add(q)
        return q

    async def unregister(self, q: asyncio.Queue):
        async with self._lock:
            self._listeners.discard(q)

    async def publish(self, event: str, data: dict):
        payload = json.dumps({"event": event, "data": data, "ts": time.time()})
        async with self._lock:
            stale = []
            for q in list(self._listeners):
                try:
                    q.put_nowait(payload)
                except Exception:
                    stale.append(q)
            for q in stale:
                self._listeners.discard(q)

broadcaster = NotificationBroadcaster()

async def _sse_generator(queue: asyncio.Queue, request: Request):
    try:
        yield b": connected to notification stream\n\n"
        while True:
            if await request.is_disconnected():
                break
            msg = await queue.get()
            yield f"data: {msg}\n\n".encode("utf-8")
    except asyncio.CancelledError:
        return

@app.get("/notifications/stream")
async def notifications_stream(request: Request, current_user: dict = Depends(get_current_user)):
    """Server-Sent Events stream for real-time notification events."""
    q = await broadcaster.register()
    await broadcaster.publish("hello", {"user": current_user.get("username"), "role": current_user.get("role")})
    async def stream():
        try:
            async for chunk in _sse_generator(q, request):
                yield chunk
        finally:
            await broadcaster.unregister(q)
    return StreamingResponse(stream(), media_type="text/event-stream")

@app.get("/auth/me")
def auth_me(current_user: dict = Depends(get_current_user)):
    """Return the currently authenticated user's basic profile (sanitized)."""
    sanitized = {k: v for k, v in current_user.items() if k not in {"password", "hashed_password"}}
    return {"success": True, "data": sanitized}

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
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        query = """
            SELECT g.grade_id, g.score, g.grade, g.grade_point, g.academic_year,
                   c.course_code, c.course_title, c.credit_hours,
                   sem.semester_name,
                   s.index_number as student_index, s.full_name as student_name
            FROM grades g
            JOIN courses c ON g.course_id = c.course_id
            JOIN student_profiles s ON g.student_id = s.student_id
            JOIN semesters sem ON g.semester_id = sem.semester_id
            WHERE s.index_number = %s
        """
        params = [index_number]
        
        if semester:
            query += " AND sem.semester_name = %s"
            params.append(semester)
        
        if academic_year:
            query += " AND g.academic_year = %s"
            params.append(academic_year)
            
        query += " ORDER BY g.academic_year DESC, sem.semester_name"
        
        cursor.execute(query, params)
        grades = cursor.fetchall()
        
        # RealDictCursor already returns dictionaries, so direct return is fine.
        return grades
        
    except Exception as e:
        logger.error(f"Error fetching student grades: {str(e)}")
        return []

def calculate_student_gpa(conn, index_number, semester=None, academic_year=None):
    """Calculate student GPA with optional filtering"""
    try:
        grades = fetch_student_grades(conn, index_number, semester, academic_year)
        if not grades:
            return {"semester_gpa": 0.0, "cumulative_gpa": 0.0, "total_credit_hours": 0, "semester_credit_hours": 0, "total_courses": 0, "grade_breakdown": []}
        
        total_points = 0.0
        total_credits = 0
        semester_points = 0.0
        semester_credits = 0
        
        for grade in grades:
            credit_hours = float(grade.get('credit_hours', 0))
            grade_point = float(grade.get('grade_point', 0.0))
            
            total_points += grade_point * credit_hours
            total_credits += credit_hours

            # If filtering by semester/academic year, these are the semester's grades
            # Otherwise, consider all grades for cumulative.
            if (semester and grade.get('semester_name') == semester) or \
               (academic_year and grade.get('academic_year') == academic_year) or \
               (not semester and not academic_year): # If no filters, all grades contribute to 'semester' for this calculation
                semester_points += grade_point * credit_hours
                semester_credits += credit_hours
        
        cumulative_gpa = round(total_points / total_credits, 2) if total_credits > 0 else 0.0
        semester_gpa = round(semester_points / semester_credits, 2) if semester_credits > 0 else 0.0

        # Fetch student name for the response
        student_profile = fetch_student_by_index_number(conn, index_number)
        student_name = student_profile['full_name'] if student_profile else "Unknown Student"
        
        return {
            "student_index": index_number,
            "student_name": student_name,
            "semester_gpa": semester_gpa,
            "cumulative_gpa": cumulative_gpa,
            "total_credit_hours": total_credits,
            "semester_credit_hours": semester_credits,
            "total_courses": len(grades),
            "grade_breakdown": grades
        }
        
    except Exception as e:
        logger.error(f"Error calculating GPA: {str(e)}")
        return {"semester_gpa": 0.0, "cumulative_gpa": 0.0, "total_credit_hours": 0, "semester_credit_hours": 0, "total_courses": 0, "grade_breakdown": []}

def insert_student_grade(conn, student_index, course_code, semester_name, score, academic_year):
    """Insert or update a student grade by resolving IDs."""
    try:
        # 1. Get student_id
        student = fetch_student_by_index_number(conn, student_index)
        if not student:
            raise ValueError(f"Student with index number {student_index} not found.")
        student_id = student['student_id']

        # 2. Get course_id
        course = fetch_course_by_code(conn, course_code)
        if not course:
            raise ValueError(f"Course with code {course_code} not found.")
        course_id = course['course_id']

        # 3. Get semester_id
        semester_obj = fetch_semester_by_name(conn, semester_name)
        if not semester_obj:
            raise ValueError(f"Semester with name {semester_name} not found.")
        semester_id = semester_obj['semester_id']

        # Calculate grade and grade point
        grade_letter = calculate_grade(score)
        grade_point = get_grade_point(score)
        
        cursor = conn.cursor()
        
        # Check if grade already exists for this student, course, and semester
        check_query = """
            SELECT grade_id FROM grades 
            WHERE student_id = %s AND course_id = %s AND semester_id = %s
        """
        cursor.execute(check_query, (student_id, course_id, semester_id))
        existing_grade_id = cursor.fetchone()
        
        if existing_grade_id:
            # Update existing grade
            update_query = """
                UPDATE grades 
                SET score = %s, grade = %s, grade_point = %s, academic_year = %s, updated_at = CURRENT_TIMESTAMP
                WHERE grade_id = %s
                RETURNING grade_id;
            """
            cursor.execute(update_query, (score, grade_letter, grade_point, academic_year, existing_grade_id[0]))
            updated_id = cursor.fetchone()[0]
            conn.commit()
            logger.info(f"Grade updated for student {student_index}, course {course_code}, semester {semester_name}. Grade ID: {updated_id}")
            return updated_id
        else:
            # Insert new grade
            insert_query = """
                INSERT INTO grades (student_id, course_id, semester_id, score, grade, grade_point, academic_year)
                VALUES (%s, %s, %s, %s, %s, %s, %s) 
                RETURNING grade_id;
            """
            cursor.execute(insert_query, (
                student_id, course_id, semester_id, score, grade_letter, grade_point, academic_year
            ))
            new_grade_id = cursor.fetchone()[0]
            conn.commit()
            logger.info(f"New grade inserted for student {student_index}, course {course_code}, semester {semester_name}. Grade ID: {new_grade_id}")
            return new_grade_id
            
    except ValueError as ve:
        logger.error(f"Data validation error in insert_student_grade: {str(ve)}")
        conn.rollback() # Ensure rollback on validation errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Error inserting/updating grade for {student_index}, {course_code}, {semester_name}: {str(e)}")
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save grade: {str(e)}"
        )

def fetch_grades_with_filters(conn, student_index=None, course_code=None, semester=None, skip=0, limit=100):
    """Fetch grades with filtering and pagination"""
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor) # Use RealDictCursor for easier dictionary access
        
        query = """
            SELECT 
                g.grade_id, g.score, g.grade, g.grade_point, g.academic_year,
                s.index_number as student_index, s.full_name as student_name,
                c.course_code, c.course_title, c.credit_hours,
                sem.semester_name
            FROM grades g
            JOIN student_profiles s ON g.student_id = s.student_id
            JOIN courses c ON g.course_id = c.course_id
            JOIN semesters sem ON g.semester_id = sem.semester_id
            WHERE 1=1
        """
        params = []
        
        if student_index:
            query += " AND s.index_number ILIKE %s" # Use ILIKE for case-insensitive search
            params.append(f"%{student_index}%")
            
        if course_code:
            query += " AND c.course_code ILIKE %s"
            params.append(f"%{course_code}%")
            
        if semester:
            query += " AND sem.semester_name ILIKE %s"
            params.append(f"%{semester}%")
        
        # Get total count
        count_query = f"SELECT COUNT(*) FROM ({query}) as filtered"
        # Remove ORDER BY and LIMIT/OFFSET for count query
        count_query_no_order_limit = count_query.split("ORDER BY")[0].split("LIMIT")[0].split("OFFSET")[0]
        
        cursor.execute(count_query_no_order_limit, params)
        total_count = cursor.fetchone()['count'] # Access count by name
        
        # Add pagination
        query += " ORDER BY s.index_number, sem.academic_year DESC, sem.semester_name, c.course_code LIMIT %s OFFSET %s"
        params.extend([limit, skip])
        
        cursor.execute(query, params)
        grades = cursor.fetchall() # Already dictionaries due to RealDictCursor
        
        return {
            "grades": grades,
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

@app.get("/frontend")
async def serve_frontend():
    """Serve the frontend application"""
    from fastapi.responses import FileResponse
    frontend_file = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
    if os.path.exists(frontend_file):
        return FileResponse(frontend_file)
    else:
        raise HTTPException(status_code=404, detail="Frontend not found")

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

@app.get("/me", response_model=APIResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user information"""
    try:
        logger.info(f"[ME] User info requested by: {current_user.get('username')}")
        logger.debug(f"[ME] Current user dict: {current_user}")
        user_info = {
            "username": current_user.get('username'),
            "role": current_user.get('role'),
            "authenticated": True
        }
        # If the user is a student, add their index number
        if current_user.get('role') == 'student':
            user_info['index_number'] = current_user.get('index_number')
        logger.debug(f"[ME] Returning user_info: {user_info}")
        return APIResponse(
            success=True,
            message="User information retrieved successfully",
            data=user_info
        )
    except Exception as e:
        logger.error(f"[ME] Error retrieving user info: {str(e)}")
        return APIResponse(
            success=False,
            message="Failed to retrieve user information",
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
            # Check if student already exists by index_number
            existing_student = fetch_student_by_index_number(conn, student.index_number)
            if existing_student:
                raise ValueError(f"Student with index number {student.index_number} already exists.")

            return insert_student_profile(
                conn, 
                student.index_number,
                student.full_name,
                datetime.strptime(student.dob, '%Y-%m-%d').date() if student.dob else None,
                student.gender,
                student.contact_email,
                student.phone,  # API field 'phone' maps to DB 'contact_phone'
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
            # This case might be hit if insert_student_profile returns False due to UniqueViolation
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create student - index number may already exist or other DB error"
            )
            
    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
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
                    # Check if student already exists by index_number
                    existing_student = fetch_student_by_index_number(conn, student.index_number)
                    if existing_student:
                        raise ValueError(f"Student with index number {student.index_number} already exists.")

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
                        "error": "Failed to create - unknown database error"
                    })
                    
            except ValueError as ve:
                failed_students.append({
                    "index_number": student.index_number,
                    "error": str(ve)
                })
                logger.warning(f"Failed to create student in bulk: {student.index_number} - {ve}")
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
        
        # fetch_all_records returns a dict with 'students' key
        all_records = handle_db_operation(fetch_all_records)
        students = all_records.get('students', []) if all_records else []
        
        if students:
            student_list = students[skip:skip+limit]
            total_count = len(students)
            
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
            cursor = conn.cursor(cursor_factory=RealDictCursor) # Use RealDictCursor
            
            base_query = """
                SELECT student_id, index_number, full_name, dob, gender, 
                       contact_email, contact_phone, program, year_of_study
                FROM student_profiles 
                WHERE 1=1
            """
            
            params = []
            conditions = []
            
            if name:
                conditions.append(" AND full_name ILIKE %s")
                params.append(f"%{name}%")
            
            if program:
                conditions.append(" AND program ILIKE %s") # Use ILIKE for program
                params.append(f"%{program}%")
            
            if year_of_study:
                conditions.append(" AND year_of_study = %s")
                params.append(year_of_study)
            
            if gender:
                conditions.append(" AND gender ILIKE %s") # Use ILIKE for gender
                params.append(f"%{gender}%")
            
            condition_string = "".join(conditions)
            full_query = base_query + condition_string + " ORDER BY full_name LIMIT %s OFFSET %s"
            full_count_query = "SELECT COUNT(*) FROM student_profiles WHERE 1=1" + condition_string
            
            # Get total count
            cursor.execute(full_count_query, params)
            total_count = cursor.fetchone()['count']
            
            # Get paginated results
            cursor.execute(full_query, params + [limit, skip])
            students_raw = cursor.fetchall()
            
            # Format DOB to string
            for student in students_raw:
                if student['dob']:
                    student['dob'] = student['dob'].strftime('%Y-%m-%d')
            
            return students_raw, total_count
        
        students_list, total_count = handle_db_operation(operation)
        
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

@app.get("/admin/search/students", response_model=APIResponse)
async def global_search_students(
    current_user: dict = Depends(require_admin_role),
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results")
):
    """Global search for students (Admin only)"""
    try:
        logger.info(f"Admin {current_user.get('username')} performing global student search for: {q}")
        
        def operation(conn):
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Search in multiple fields
            query = """
                SELECT student_id, index_number, full_name, program, year_of_study, contact_email
                FROM student_profiles 
                WHERE full_name ILIKE %s 
                   OR index_number ILIKE %s 
                   OR program ILIKE %s 
                   OR contact_email ILIKE %s
                ORDER BY 
                    CASE 
                        WHEN full_name ILIKE %s THEN 1
                        WHEN index_number ILIKE %s THEN 2
                        WHEN program ILIKE %s THEN 3
                        ELSE 4
                    END,
                    full_name
                LIMIT %s
            """
            
            search_pattern = f"%{q}%"
            exact_pattern = f"{q}%"
            
            cursor.execute(query, [
                search_pattern, search_pattern, search_pattern, search_pattern,
                exact_pattern, exact_pattern, exact_pattern,
                limit
            ])
            
            return cursor.fetchall()
        
        results = handle_db_operation(operation)
        
        return APIResponse(
            success=True,
            message=f"Found {len(results)} students matching '{q}'",
            data={"results": results}
        )
        
    except Exception as e:
        logger.error(f"Global student search failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Global student search failed: {str(e)}"
        )

@app.get("/admin/search/courses", response_model=APIResponse)
async def global_search_courses(
    current_user: dict = Depends(require_admin_role),
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results")
):
    """Global search for courses (Admin only)"""
    try:
        logger.info(f"Admin {current_user.get('username')} performing global course search for: {q}")
        
        def operation(conn):
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Search in multiple fields
            query = """
                SELECT course_id, course_code, course_title, credit_hours, department
                FROM courses 
                WHERE course_title ILIKE %s 
                   OR course_code ILIKE %s 
                   OR department ILIKE %s
                ORDER BY 
                    CASE 
                        WHEN course_title ILIKE %s THEN 1
                        WHEN course_code ILIKE %s THEN 2
                        WHEN department ILIKE %s THEN 3
                        ELSE 4
                    END,
                    course_title
                LIMIT %s
            """
            
            search_pattern = f"%{q}%"
            exact_pattern = f"{q}%"
            
            cursor.execute(query, [
                search_pattern, search_pattern, search_pattern,
                exact_pattern, exact_pattern, exact_pattern,
                limit
            ])
            
            return cursor.fetchall()
        
        results = handle_db_operation(operation)
        
        return APIResponse(
            success=True,
            message=f"Found {len(results)} courses matching '{q}'",
            data={"results": results}
        )
        
    except Exception as e:
        logger.error(f"Global course search failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Global course search failed: {str(e)}"
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
            student = fetch_student_by_index_number(conn, index_number)
            if student and student.get('dob'):
                student['dob'] = student['dob'].strftime('%Y-%m-%d')
            return student
        
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
        
        def operation(conn):
            # Fetch student_id using index_number
            student = fetch_student_by_index_number(conn, index_number)
            if not student:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Student with index number {index_number} not found"
                )
            student_id = student['student_id']

            # Prepare updates dictionary, converting DOB if present
            updates = student_update.dict(exclude_unset=True)
            if 'dob' in updates and updates['dob'] is not None:
                try:
                    updates['dob'] = datetime.strptime(updates['dob'], '%Y-%m-%d').date()
                except ValueError:
                    raise ValueError('Date of birth must be in YYYY-MM-DD format')
            elif 'dob' in updates and updates['dob'] is None:
                updates['dob'] = None # Allow setting DOB to null

            # Call the db function to update the student profile
            success = update_student_profile(conn, student_id, updates)
            if not success:
                raise Exception("Database update operation failed.")
            return success
        
        handle_db_operation(operation)
        
        logger.info(f"Student updated successfully: {index_number}")
        return APIResponse(
            success=True,
            message="Student updated successfully",
            data={"index_number": index_number}
        )
            
    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Failed to update student {index_number}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update student: {str(e)}"
        )

@app.delete("/admin/students/{index_number}", response_model=APIResponse)
async def delete_student(
    index_number: str = Path(..., description="Student index number"),
    current_user: dict = Depends(require_admin_role)
):
    """Delete student profile (Admin only)"""
    try:
        logger.info(f"Admin {current_user.get('username')} deleting student: {index_number}")
        
        def operation(conn):
            # Fetch student_id using index_number
            student = fetch_student_by_index_number(conn, index_number)
            if not student:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Student with index number {index_number} not found"
                )
            student_id = student['student_id']
            return delete_student_profile(conn, student_id)
        
        success = handle_db_operation(operation)
        
        if success:
            logger.info(f"Student deleted successfully: {index_number}")
            return APIResponse(
                success=True,
                message="Student deleted successfully",
                data={"index_number": index_number}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student with index number {index_number} not found or could not be deleted"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete student {index_number}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete student: {str(e)}"
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
            # Check if course already exists by course_code
            existing_course = fetch_course_by_code(conn, course.course_code)
            if existing_course:
                raise ValueError(f"Course with code {course.course_code} already exists.")

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
                detail="Failed to create course - course code may already exist or other DB error"
            )
            
    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
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
        
        # fetch_all_records returns a dict with 'courses' key
        all_records = handle_db_operation(fetch_all_records)
        courses = all_records.get('courses', []) if all_records else []
        
        if courses:
            course_list = courses[skip:skip+limit]
            total_count = len(courses)
            
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

@app.put("/admin/courses/{course_code}", response_model=APIResponse)
async def update_course_endpoint(
    course_update: CourseCreate, # Reusing CourseCreate for update, assuming all fields can be updated
    course_code: str = Path(..., description="Course code of the course to update"),
    current_user: dict = Depends(require_admin_role)
):
    """Update course details (Admin only)"""
    try:
        logger.info(f"Admin {current_user.get('username')} updating course: {course_code}")
        
        def operation(conn):
            # Fetch course_id using course_code
            course = fetch_course_by_code(conn, course_code)
            if not course:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Course with code {course_code} not found"
                )
            course_id = course['course_id']

            updates = course_update.dict(exclude_unset=True)
            # Ensure course_code is not updated if it's the identifier
            if 'course_code' in updates:
                del updates['course_code']

            success = update_course(conn, course_id, updates)
            if not success:
                raise Exception("Database update operation failed.")
            return success
        
        handle_db_operation(operation)
        
        logger.info(f"Course {course_code} updated successfully")
        return APIResponse(
            success=True,
            message="Course updated successfully",
            data={"course_code": course_code}
        )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update course {course_code}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update course: {str(e)}"
        )

@app.delete("/admin/courses/{course_code}", response_model=APIResponse)
async def delete_course_endpoint(
    course_code: str = Path(..., description="Course code of the course to delete"),
    current_user: dict = Depends(require_admin_role)
):
    """Delete a course (Admin only)"""
    try:
        logger.info(f"Admin {current_user.get('username')} deleting course: {course_code}")
        
        def operation(conn):
            # Fetch course_id using course_code
            course = fetch_course_by_code(conn, course_code)
            if not course:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Course with code {course_code} not found"
                )
            course_id = course['course_id']
            return delete_course(conn, course_id)
        
        success = handle_db_operation(operation)
        
        if success:
            logger.info(f"Course {course_code} deleted successfully")
            return APIResponse(
                success=True,
                message="Course deleted successfully",
                data={"course_code": course_code}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with code {course_code} not found or could not be deleted"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete course {course_code}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete course: {str(e)}"
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
            # Check if semester already exists by name
            existing_semester = fetch_semester_by_name(conn, semester.semester_name)
            if existing_semester:
                raise ValueError(f"Semester with name {semester.semester_name} already exists.")

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
                detail="Failed to create semester - semester name may already exist or other DB error"
            )
            
    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
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
        
        # fetch_all_records returns a dict with 'semesters' key
        all_records = handle_db_operation(fetch_all_records)
        semesters = all_records.get('semesters', []) if all_records else []
        
        if semesters:
            logger.info(f"Retrieved {len(semesters)} semesters")
            return APIResponse(
                success=True,
                message=f"Retrieved {len(semesters)} semesters",
                data={"semesters": semesters}
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

@app.put("/admin/semesters/{semester_name}", response_model=APIResponse)
async def update_semester_endpoint(
    semester_update: SemesterCreate, # Reusing SemesterCreate for update
    semester_name: str = Path(..., description="Name of the semester to update"),
    current_user: dict = Depends(require_admin_role)
):
    """Update semester details (Admin only)"""
    try:
        logger.info(f"Admin {current_user.get('username')} updating semester: {semester_name}")
        
        def operation(conn):
            # Fetch semester_id using semester_name
            semester_obj = fetch_semester_by_name(conn, semester_name)
            if not semester_obj:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Semester with name {semester_name} not found"
                )
            semester_id = semester_obj['semester_id']

            updates = semester_update.dict(exclude_unset=True)
            # Ensure semester_name is not updated if it's the identifier in the path
            if 'semester_name' in updates:
                del updates['semester_name']
            
            # Convert date strings to date objects if present
            if 'start_date' in updates and updates['start_date'] is not None:
                try:
                    updates['start_date'] = datetime.strptime(updates['start_date'], '%Y-%m-%d').date()
                except ValueError:
                    raise ValueError('Start date must be in YYYY-MM-DD format')
            if 'end_date' in updates and updates['end_date'] is not None:
                try:
                    updates['end_date'] = datetime.strptime(updates['end_date'], '%Y-%m-%d').date()
                except ValueError:
                    raise ValueError('End date must be in YYYY-MM-DD format')

            success = update_semester(conn, semester_id, updates)
            if not success:
                raise Exception("Database update operation failed.")
            return success
        
        handle_db_operation(operation)
        
        logger.info(f"Semester {semester_name} updated successfully")
        return APIResponse(
            success=True,
            message="Semester updated successfully",
            data={"semester_name": semester_name}
        )
            
    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Failed to update semester {semester_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update semester: {str(e)}"
        )

@app.delete("/admin/semesters/{semester_name}", response_model=APIResponse)
async def delete_semester_endpoint(
    semester_name: str = Path(..., description="Name of the semester to delete"),
    current_user: dict = Depends(require_admin_role)
):
    """Delete a semester (Admin only)"""
    try:
        logger.info(f"Admin {current_user.get('username')} deleting semester: {semester_name}")
        
        def operation(conn):
            # Fetch semester_id using semester_name
            semester_obj = fetch_semester_by_name(conn, semester_name)
            if not semester_obj:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Semester with name {semester_name} not found"
                )
            semester_id = semester_obj['semester_id']
            return delete_semester(conn, semester_id)
        
        success = handle_db_operation(operation)
        
        if success:
            logger.info(f"Semester {semester_name} deleted successfully")
            return APIResponse(
                success=True,
                message="Semester deleted successfully",
                data={"semester_name": semester_name}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Semester with name {semester_name} not found or could not be deleted"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete semester {semester_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete semester: {str(e)}"
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
            student = fetch_student_by_index_number(conn, index_number)
            if student and student.get('dob'):
                student['dob'] = student['dob'].strftime('%Y-%m-%d')
            return student
        
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
async def get_student_grades_endpoint(
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
async def get_student_gpa_endpoint(
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
                data={"semester_gpa": 0.0, "cumulative_gpa": 0.0, "total_credit_hours": 0, "semester_credit_hours": 0, "total_courses": 0, "grade_breakdown": []}
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
async def create_grade_endpoint(
    grade: GradeCreate, 
    current_user: dict = Depends(require_admin_role)
):
    """Create or update a student grade (Admin only)"""
    try:
        logger.info(f"Admin {current_user.get('username')} creating/updating grade for student: {grade.student_index}")
        
        # The insert_student_grade function in db.py now handles ID resolution
        def operation(conn):
            # This function will now handle fetching student_id, course_id, semester_id internally
            # and then call db.insert_grade or db.update_student_score as appropriate.
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
            logger.info(f"Grade created/updated successfully for {grade.student_index} in {grade.course_code}. Grade ID: {grade_id}")
            return APIResponse(
                success=True,
                message="Grade created/updated successfully",
                data={"grade_id": grade_id, "student_index": grade.student_index}
            )
        else:
            # This case might be hit if insert_student_grade fails for reasons not caught by HTTPExceptions
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to save grade - check logs for details."
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Grade save operation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Grade save operation failed: {str(e)}"
        )

@app.get("/admin/grades", response_model=APIResponse)
async def get_all_grades_endpoint(
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
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch grades: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch grades: {str(e)}"
        )

@app.put("/admin/grades/{grade_id}", response_model=APIResponse)
async def update_grade_endpoint(
    grade_id: str,
    grade_update: dict,
    current_user: dict = Depends(require_admin_role)
):
    """Update an existing grade (Admin only)"""
    try:
        logger.info(f"Admin {current_user.get('username')} updating grade: {grade_id}")
        
        def operation(conn):
            cursor = conn.cursor()
            
            # Check if grade exists
            cursor.execute("SELECT grade_id FROM grades WHERE grade_id = %s", (grade_id,))
            if not cursor.fetchone():
                raise ValueError(f"Grade with ID {grade_id} not found")
            
            # Build update query dynamically
            update_fields = []
            values = []
            
            # If score is provided, recalculate letter grade and grade point
            if 'score' in grade_update:
                score = grade_update['score']
                letter_grade = calculate_grade(score)
                grade_point = get_grade_point(score)
                
                update_fields.extend(["score = %s", "grade = %s", "grade_point = %s"])
                values.extend([score, letter_grade, grade_point])
            else:
                # Fallback to direct letter grade and grade point updates
                if 'letter_grade' in grade_update:
                    update_fields.append("grade = %s")
                    values.append(grade_update['letter_grade'])
                
                if 'grade_point' in grade_update:
                    update_fields.append("grade_point = %s")
                    values.append(grade_update['grade_point'])
            
            if not update_fields:
                raise ValueError("No valid fields to update")
            
            values.append(grade_id)
            
            update_query = f"""
                UPDATE grades 
                SET {', '.join(update_fields)}
                WHERE grade_id = %s
            """
            
            cursor.execute(update_query, values)
            
            if cursor.rowcount == 0:
                raise ValueError("No grade was updated")
            
            conn.commit()
            return cursor.rowcount
        
        updated_count = handle_db_operation(operation)
        
        if updated_count:
            logger.info(f"Grade {grade_id} updated successfully")
            return APIResponse(
                success=True,
                message="Grade updated successfully",
                data={"grade_id": grade_id, "updated_fields": list(grade_update.keys())}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Grade not found or no changes made"
            )
            
    except ValueError as ve:
        logger.error(f"Validation error updating grade {grade_id}: {str(ve)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update grade {grade_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Grade update failed: {str(e)}"
        )

@app.delete("/admin/grades/{grade_id}", response_model=APIResponse)
async def delete_grade_endpoint(
    grade_id: str,
    current_user: dict = Depends(require_admin_role)
):
    """Delete an existing grade (Admin only)"""
    try:
        logger.info(f"Admin {current_user.get('username')} deleting grade: {grade_id}")
        
        def operation(conn):
            cursor = conn.cursor()
            
            # Check if grade exists
            cursor.execute("SELECT grade_id FROM grades WHERE grade_id = %s", (grade_id,))
            if not cursor.fetchone():
                raise ValueError(f"Grade with ID {grade_id} not found")
            
            # Delete the grade
            cursor.execute("DELETE FROM grades WHERE grade_id = %s", (grade_id,))
            
            if cursor.rowcount == 0:
                raise ValueError("No grade was deleted")
            
            conn.commit()
            return cursor.rowcount
        
        deleted_count = handle_db_operation(operation)
        
        if deleted_count:
            logger.info(f"Grade {grade_id} deleted successfully")
            return APIResponse(
                success=True,
                message="Grade deleted successfully",
                data={"grade_id": grade_id}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Grade not found"
            )
            
    except ValueError as ve:
        logger.error(f"Validation error deleting grade {grade_id}: {str(ve)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete grade {grade_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Grade deletion failed: {str(e)}"
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
                conn,
                student_account.index_number, 
                student_account.full_name
            )
        
        result = handle_db_operation(operation)
        
        if result and len(result) == 2:
            success, data = result
            if success:
                logger.info(f"Student account created successfully: {student_account.index_number}")
                return APIResponse(
                    success=True,
                    message="Student account created successfully",
                    data={
                        "index_number": student_account.index_number,
                        "username": student_account.index_number,
                        "password_generated": True # Assuming password was generated if not provided
                    }
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to create student account: {data}"
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
        
        if result and len(result) == 2:
            success, data = result
            if success:
                logger.info(f"Password reset successfully: {password_reset.index_number}")
                return APIResponse(
                    success=True,
                    message="Password reset successfully",
                    data={
                        "index_number": password_reset.index_number,
                        "new_password": data if isinstance(data, str) else "Generated automatically"
                    }
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Student account not found: {data}"
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
            # Pass connection to bulk_import_from_file
            return bulk_import_from_file(conn, bulk_data.file_data, bulk_data.semester_name)
        
        result = handle_db_operation(operation)
        
        if result:
            logger.info(f"Bulk import completed: {result.get('successful_imports', 0)} records")
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
async def generate_summary_report_endpoint(
    current_user: dict = Depends(require_admin_role),
    semester: Optional[str] = Query(None, description="Filter by semester"),
    academic_year: Optional[str] = Query(None, description="Filter by academic year"),
    format: str = Query("json", description="Report format (json/pdf/txt)")
):
    """Generate comprehensive summary report (Admin only)"""
    return await generate_summary_report_common(current_user, semester, academic_year, format)

@app.get("/admin/reports/summary/pdf")
async def generate_summary_report_pdf_endpoint(
    current_user: dict = Depends(require_admin_role),
    semester: Optional[str] = Query(None, description="Filter by semester"),
    academic_year: Optional[str] = Query(None, description="Filter by academic year")
):
    """Generate comprehensive summary report in PDF format (Admin only)"""
    return await generate_summary_report_common(current_user, semester, academic_year, "pdf")

@app.get("/admin/reports/summary/txt")
async def generate_summary_report_txt_endpoint(
    current_user: dict = Depends(require_admin_role),
    semester: Optional[str] = Query(None, description="Filter by semester"),
    academic_year: Optional[str] = Query(None, description="Filter by academic year")
):
    """Generate comprehensive summary report in TXT format (Admin only)"""
    return await generate_summary_report_common(current_user, semester, academic_year, "txt")

@app.get("/admin/reports/summary/excel")
async def generate_summary_report_excel_endpoint(
    current_user: dict = Depends(require_admin_role),
    semester: Optional[str] = Query(None, description="Filter by semester"),
    academic_year: Optional[str] = Query(None, description="Filter by academic year")
):
    """Generate comprehensive summary report in Excel format (Admin only).
    Direct in-memory construction (multi-sheet) to avoid temp files. Returns raw bytes Response with
    explicit Content-Length for maximal browser compatibility.
    Sheets:
      - Summary: high-level stats & filters
      - GradeDistribution: grade counts
    """
    from io import BytesIO
    import xlsxwriter
    try:
        logger.info("[ExcelDownload] Building excel directly without intermediate JSON call")

        # Re-run core data logic manually (subset of generate_comprehensive_report) to avoid re-parsing
        def op(conn):
            return generate_comprehensive_report(conn, semester, academic_year, "json")
        core_data = handle_db_operation(op)
        if not core_data:
            logger.warning("[ExcelDownload] core_data is empty; continuing with placeholder workbook")
            core_data = {}

        stats = core_data.get("summary_statistics", {}) if isinstance(core_data, dict) else {}
        grade_distribution = core_data.get("grade_distribution", {}) if isinstance(core_data, dict) else {}
        avg_gpa = core_data.get("average_gpa", 0)
        filters = core_data.get("filters", {"semester": semester, "academic_year": academic_year})

        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})

        # Formats
        fmt_header = workbook.add_format({"bold": True, "bg_color": "#D9E1F2"})
        fmt_key = workbook.add_format({"bold": True})
        fmt_num = workbook.add_format({"num_format": "0.00"})

        # Summary sheet
        ws_summary = workbook.add_worksheet("Summary")
        row = 0
        ws_summary.write(row, 0, "Metric", fmt_header)
        ws_summary.write(row, 1, "Value", fmt_header)
        row += 1
        for k, v in stats.items():
            ws_summary.write(row, 0, k, fmt_key)
            ws_summary.write(row, 1, v)
            row += 1
        ws_summary.write(row, 0, "average_gpa", fmt_key)
        ws_summary.write(row, 1, avg_gpa, fmt_num)
        row += 2
        ws_summary.write(row, 0, "Filters", fmt_header); row += 1
        ws_summary.write(row, 0, "semester", fmt_key); ws_summary.write(row, 1, str(filters.get("semester"))) ; row +=1
        ws_summary.write(row, 0, "academic_year", fmt_key); ws_summary.write(row, 1, str(filters.get("academic_year"))) ; row +=1
        ws_summary.write(row, 0, "generated_at", fmt_key); ws_summary.write(row, 1, core_data.get("generated_at", "")); row +=1
        ws_summary.set_column(0, 0, 24)
        ws_summary.set_column(1, 1, 32)

        # Grade distribution sheet
        ws_dist = workbook.add_worksheet("GradeDistribution")
        ws_dist.write(0, 0, "Grade", fmt_header)
        ws_dist.write(0, 1, "Count", fmt_header)
        r = 1
        for grade, count in grade_distribution.items():
            ws_dist.write(r, 0, grade)
            ws_dist.write(r, 1, count)
            r += 1
        ws_dist.autofilter(0, 0, max(r-1,0), 1)
        ws_dist.set_column(0, 0, 12)
        ws_dist.set_column(1, 1, 12)

        workbook.close()
        output.seek(0)
        data = output.getvalue()
        size = len(data)
        logger.info(f"[ExcelDownload] Final workbook size={size} bytes; stats_keys={list(stats.keys())}; grades={len(grade_distribution)}")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"summary_report_{timestamp}.xlsx"
        headers = {
            "Content-Disposition": f"attachment; filename=\"{filename}\"",
            "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "Content-Length": str(size),
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            "X-Debug-Excel-Size": str(size),
            "Access-Control-Expose-Headers": "Content-Disposition, Content-Type, Content-Length, X-Debug-Excel-Size"
        }
        logger.info(f"[ExcelDownload] Returning excel with headers: {headers}")
        # Direct Response (not StreamingResponse) for explicit content-length behavior
        return Response(content=data, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers=headers)
    except Exception as e:
        logger.exception(f"[ExcelDownload] Direct build failed: {e}; falling back to legacy file path mechanism")
        return await generate_summary_report_common(current_user, semester, academic_year, "excel")

@app.get("/admin/reports/summary/csv")
async def generate_summary_report_csv_endpoint(
    current_user: dict = Depends(require_admin_role),
    semester: Optional[str] = Query(None, description="Filter by semester"),
    academic_year: Optional[str] = Query(None, description="Filter by academic year")
):
    """Generate comprehensive summary report in CSV format (Admin only)"""
    return await generate_summary_report_common(current_user, semester, academic_year, "csv")

@app.get("/admin/reports/transcript/{student_index}")
async def generate_academic_transcript(
    student_index: str,
    current_user: dict = Depends(require_admin_role),
    format: str = Query("excel", description="Export format (excel|pdf)")
):
    """Generate individual student academic transcript (Admin only)

    Returns JSON metadata for excel (current pattern) or direct PDF file response.
    """
    try:
        logger.info(f"Admin {current_user.get('username')} generating transcript for {student_index} format={format}")
        if format == "excel":
            filename = export_academic_transcript_excel(student_index)
            if not filename:
                raise HTTPException(status_code=500, detail="Failed to generate academic transcript (excel)")
            return APIResponse(
                success=True,
                message="Academic transcript generated successfully in Excel format",
                data={"filename": filename, "student_index": student_index, "format": format}
            )
        elif format == "pdf":
            filename = export_academic_transcript_pdf(student_index)
            if not filename:
                raise HTTPException(status_code=500, detail="Failed to generate academic transcript (pdf)")
            try:
                with open(filename, 'rb') as f:
                    data = f.read()
            except FileNotFoundError:
                raise HTTPException(status_code=500, detail="Transcript PDF disappeared before sending")
            headers = {
                "Content-Disposition": f"attachment; filename=\"{filename}\"",
                "Content-Type": "application/pdf",
                "Cache-Control": "no-cache"
            }
            return Response(content=data, media_type="application/pdf", headers=headers)
        else:
            raise HTTPException(status_code=400, detail="Invalid format. Use excel or pdf")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Academic transcript generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Academic transcript generation failed: {str(e)}")

async def generate_summary_report_common(
    current_user: dict,
    semester: Optional[str] = None,
    academic_year: Optional[str] = None,
    format: str = "json"
):
    """Generate comprehensive summary report (Admin only)"""
    try:
        logger.info(f"Admin {current_user.get('username')} generating summary report in {format} format")
        
        if format not in ["json", "pdf", "txt", "excel", "csv"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid format. Supported formats: json, pdf, txt, excel, csv"
            )
        
        # Always build core data in JSON mode to obtain records/aggregates
        def op(conn):
            return generate_comprehensive_report(conn, semester, academic_year, "json")
        core_json = handle_db_operation(op)

        if format == "json":
            if not core_json:
                return APIResponse(success=True, message="No data available for report generation", data={"report": "No data available"})
            return APIResponse(success=True, message="Summary report generated successfully (json)", data=core_json)

        if format == "excel":
            # Delegate to dedicated excel endpoint logic (caller already uses separate route)
            # Keeping legacy behavior: return metadata not file here.
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            return APIResponse(success=True, message="Use /admin/reports/summary/excel for excel bytes", data={"hint": "Call dedicated excel endpoint", "generated_at": timestamp})

        # Handle pdf/txt/csv via unified helper
        if format in {"pdf", "txt", "csv"}:
            from report_utils import build_summary_file
            built = build_summary_file(format)
            if not built:
                raise HTTPException(status_code=500, detail=f"Failed to generate {format} summary report")
            content_bytes, filename, media_type = built
            headers = {
                "Content-Disposition": f"attachment; filename=\"{filename}\"",
                "Content-Type": media_type,
                "Content-Length": str(len(content_bytes)),
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
                "Access-Control-Expose-Headers": "Content-Disposition, Content-Type, Content-Length"
            }
            logger.info(f"Returning unified {format} summary report size={len(content_bytes)} bytes")
            return Response(content=content_bytes, media_type=media_type, headers=headers)

        raise HTTPException(status_code=400, detail="Unsupported format")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Report generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report generation failed: {str(e)}"
        )

# STUDENT ENDPOINTS - PERSONAL REPORTS
@app.get("/student/report/pdf")
async def download_student_personal_report_pdf(
    current_user: dict = Depends(require_student_role)
):
    """Download personal academic report in PDF format (Student only)"""
    try:
        logger.info(f"Student {current_user.get('username')} downloading personal PDF report")
        
        # Get student's index number from their profile
        student_index = current_user.get('user_data', {}).get('index_number')
        if not student_index:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student index number not found in profile"
            )
        
        # Import the personal report function
        from report_utils import export_personal_academic_report
        
        pdf_path = export_personal_academic_report(student_index, 'pdf')
        
        if pdf_path and os.path.exists(pdf_path):
            # Read the file content
            with open(pdf_path, "rb") as f:
                file_content = f.read()
            
            # Clean up the file after reading
            try:
                os.remove(pdf_path)
            except Exception as e:
                logger.warning(f"Failed to remove temporary file {pdf_path}: {e}")
            
            # Return the file content directly
            return Response(
                content=file_content,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename=personal_academic_report_{student_index}.pdf"
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unable to generate personal academic report"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Personal PDF report generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Personal PDF report generation failed: {str(e)}"
        )

@app.get("/student/report/txt")
async def download_student_personal_report_txt(
    current_user: dict = Depends(require_student_role)
):
    """Download personal academic report in TXT format (Student only)"""
    try:
        logger.info(f"Student {current_user.get('username')} downloading personal TXT report")
        
        # Get student's index number from their profile
        student_index = current_user.get('user_data', {}).get('index_number')
        if not student_index:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student index number not found in profile"
            )
        
        # Import the personal report function
        from report_utils import export_personal_academic_report
        
        txt_content = export_personal_academic_report(student_index, 'txt')
        
        if txt_content:
            # Return the file content directly
            return Response(
                content=txt_content.encode('utf-8'),
                media_type="text/plain",
                headers={
                    "Content-Disposition": f"attachment; filename=personal_academic_report_{student_index}.txt"
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unable to generate personal academic report"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Personal TXT report generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Personal TXT report generation failed: {str(e)}"
        )

# ADMIN ENDPOINT - PERSONAL REPORTS (added to satisfy export tests expecting /admin/reports/personal)
@app.get("/admin/reports/personal/{student_index}")
async def admin_personal_report(
    student_index: str,
    format: str = Query("txt", description="Report format: txt or pdf", pattern="^(txt|pdf)$"),
    current_user: dict = Depends(require_admin_role)
):
    """Generate a personal academic report for a specific student (Admin only).
    Supports txt (default) or pdf.
    """
    try:
        logger.info(f"Admin {current_user.get('username')} generating personal report for {student_index} as {format}")
        from report_utils import export_personal_academic_report
        
        if format == 'pdf':
            pdf_path = export_personal_academic_report(student_index, 'pdf')
            if not pdf_path or not os.path.exists(pdf_path):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unable to generate personal PDF report")
            with open(pdf_path, 'rb') as f:
                content = f.read()
            try:
                os.remove(pdf_path)
            except Exception as e:
                logger.warning(f"Failed to remove temporary file {pdf_path}: {e}")
            return Response(
                content=content,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename=personal_academic_report_{student_index}.pdf"
                }
            )
        else:  # txt format
            txt_content = export_personal_academic_report(student_index, 'txt')
            if not txt_content:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unable to generate personal TXT report")
            return Response(
                content=txt_content.encode('utf-8'),
                media_type="text/plain",
                headers={
                    "Content-Disposition": f"attachment; filename=personal_academic_report_{student_index}.txt"
                }
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Admin personal report generation failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Admin personal report generation failed: {e}")

@app.get("/admin/analytics/dashboard", response_model=APIResponse)
async def get_admin_dashboard_endpoint(
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

@app.get("/admin/analytics/gpa-stats", response_model=APIResponse)
async def get_gpa_stats(current_user: dict = Depends(require_admin_role)):
    """Get overall GPA statistics (Admin only)"""
    try:
        logger.info(f"Admin {current_user.get('username')} accessing GPA statistics")
        
        def operation(conn):
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT 
                    AVG(grade_point) as average_gpa,
                    MIN(grade_point) as min_gpa,
                    MAX(grade_point) as max_gpa,
                    COUNT(*) as total_grades
                FROM grades 
                WHERE grade_point IS NOT NULL
            """)
            return cursor.fetchone()
        
        stats = handle_db_operation(operation)
        
        # Convert to float for JSON serialization
        if stats and stats['average_gpa']:
            stats['average_gpa'] = float(stats['average_gpa'])
            stats['min_gpa'] = float(stats['min_gpa'])
            stats['max_gpa'] = float(stats['max_gpa'])
        
        return APIResponse(
            success=True,
            message="GPA statistics retrieved successfully",
            data=stats
        )
        
    except Exception as e:
        logger.error(f"GPA statistics failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"GPA statistics failed: {str(e)}"
        )

@app.get("/admin/analytics/grade-distribution", response_model=APIResponse)
async def get_grade_distribution(current_user: dict = Depends(require_admin_role)):
    """Get grade distribution for charts (Admin only)"""
    try:
        logger.info(f"Admin {current_user.get('username')} accessing grade distribution")
        
        def operation(conn):
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT 
                    grade, 
                    COUNT(*) as count
                FROM grades 
                WHERE grade IS NOT NULL
                GROUP BY grade
                ORDER BY grade
            """)
            results = cursor.fetchall()
            
            labels = [row['grade'] for row in results]
            values = [row['count'] for row in results]
            
            return {"labels": labels, "values": values}
        
        distribution = handle_db_operation(operation)
        
        return APIResponse(
            success=True,
            message="Grade distribution retrieved successfully",
            data=distribution
        )
        
    except Exception as e:
        logger.error(f"Grade distribution failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Grade distribution failed: {str(e)}"
        )

@app.get("/admin/analytics/gpa-trends", response_model=APIResponse)
async def get_gpa_trends(current_user: dict = Depends(require_admin_role)):
    """Get GPA trends by semester (Admin only)"""
    try:
        logger.info(f"Admin {current_user.get('username')} accessing GPA trends")
        
        def operation(conn):
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT 
                    s.semester_name,
                    s.academic_year,
                    AVG(g.grade_point) as avg_gpa
                FROM grades g
                JOIN semesters s ON g.semester_id = s.semester_id
                WHERE g.grade_point IS NOT NULL
                GROUP BY s.semester_id, s.semester_name, s.academic_year
                ORDER BY s.academic_year, s.semester_name
            """)
            results = cursor.fetchall()
            
            semesters = [f"{row['semester_name']} {row['academic_year']}" for row in results]
            gpa_values = [float(row['avg_gpa']) if row['avg_gpa'] else 0 for row in results]
            
            return {"semesters": semesters, "gpa_values": gpa_values}
        
        trends = handle_db_operation(operation)
        
        return APIResponse(
            success=True,
            message="GPA trends retrieved successfully",
            data=trends
        )
        
    except Exception as e:
        logger.error(f"GPA trends failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"GPA trends failed: {str(e)}"
        )

@app.get("/admin/analytics/program-performance", response_model=APIResponse)
async def get_program_performance(current_user: dict = Depends(require_admin_role)):
    """Get performance by academic program (Admin only)"""
    try:
        logger.info(f"Admin {current_user.get('username')} accessing program performance")
        
        def operation(conn):
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT 
                    st.program,
                    AVG(g.grade_point) as avg_gpa,
                    COUNT(g.grade_id) as total_grades
                FROM grades g
                JOIN student_profiles st ON g.student_id = st.student_id
                WHERE g.grade_point IS NOT NULL AND st.program IS NOT NULL
                GROUP BY st.program
                HAVING COUNT(g.grade_id) >= 5
                ORDER BY avg_gpa DESC
                LIMIT 10
            """)
            results = cursor.fetchall()
            
            programs = [row['program'] for row in results]
            gpa_values = [float(row['avg_gpa']) if row['avg_gpa'] else 0 for row in results]
            
            return {"programs": programs, "gpa_values": gpa_values}
        
        performance = handle_db_operation(operation)
        
        return APIResponse(
            success=True,
            message="Program performance retrieved successfully",
            data=performance
        )
        
    except Exception as e:
        logger.error(f"Program performance failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Program performance failed: {str(e)}"
        )

@app.get("/admin/analytics/dashboard-insights", response_model=APIResponse)
async def get_dashboard_insights(current_user: dict = Depends(require_admin_role)):
    """Get comprehensive dashboard insights (Admin only)"""
    try:
        logger.info(f"Admin {current_user.get('username')} accessing dashboard insights")
        
        def operation(conn):
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get recent activity (last 10 grades added)
            cursor.execute("""
                SELECT 
                    sp.full_name as student_name,
                    c.course_title as course_name,
                    g.grade,
                    g.created_at
                FROM grades g
                JOIN student_profiles sp ON g.student_id = sp.student_id
                JOIN courses c ON g.course_id = c.course_id
                ORDER BY g.created_at DESC
                LIMIT 5
            """)
            recent_activities = cursor.fetchall()
            
            # Get semester with most activity
            cursor.execute("""
                SELECT 
                    s.semester_name,
                    s.academic_year,
                    COUNT(g.grade_id) as grade_count
                FROM semesters s
                LEFT JOIN grades g ON s.semester_id = g.semester_id
                GROUP BY s.semester_id, s.semester_name, s.academic_year
                ORDER BY grade_count DESC
                LIMIT 1
            """)
            active_semester = cursor.fetchone()
            
            # Get grade distribution summary
            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN grade = 'A' THEN 1 END) as a_count,
                    COUNT(CASE WHEN grade = 'B' THEN 1 END) as b_count,
                    COUNT(CASE WHEN grade = 'C' THEN 1 END) as c_count,
                    COUNT(CASE WHEN grade = 'D' THEN 1 END) as d_count,
                    COUNT(CASE WHEN grade = 'F' THEN 1 END) as f_count,
                    COUNT(*) as total_grades
                FROM grades
                WHERE grade IS NOT NULL
            """)
            grade_summary = cursor.fetchone()
            
            return {
                "recent_activities": recent_activities,
                "active_semester": active_semester,
                "grade_summary": grade_summary
            }
        
        insights = handle_db_operation(operation)
        
        return APIResponse(
            success=True,
            message="Dashboard insights retrieved successfully",
            data=insights
        )
        
    except Exception as e:
        logger.error(f"Dashboard insights failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dashboard insights failed: {str(e)}"
        )

@app.get("/admin/analytics/course-enrollment", response_model=APIResponse)
async def get_course_enrollment(current_user: dict = Depends(require_admin_role)):
    """Get course enrollment statistics (Admin only)"""
    try:
        logger.info(f"Admin {current_user.get('username')} accessing course enrollment")
        
        def operation(conn):
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT 
                    c.course_title,
                    c.course_code,
                    COUNT(g.grade_id) as enrollment_count
                FROM courses c
                LEFT JOIN grades g ON c.course_id = g.course_id
                GROUP BY c.course_id, c.course_title, c.course_code
                HAVING COUNT(g.grade_id) > 0
                ORDER BY enrollment_count DESC
                LIMIT 10
            """)
            results = cursor.fetchall()
            
            courses = [f"{row['course_code']} - {row['course_title']}" for row in results]
            enrollment_counts = [row['enrollment_count'] for row in results]
            
            return {"courses": courses, "enrollment_counts": enrollment_counts}
        
        enrollment = handle_db_operation(operation)
        
        return APIResponse(
            success=True,
            message="Course enrollment retrieved successfully",
            data=enrollment
        )
        
    except Exception as e:
        logger.error(f"Course enrollment failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Course enrollment failed: {str(e)}"
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
            cursor = conn.cursor(cursor_factory=RealDictCursor) # Use RealDictCursor
            cursor.execute("""
                SELECT semester_id, semester_name, academic_year, start_date, end_date 
                FROM semesters 
                ORDER BY start_date DESC
            """)
            semesters_raw = cursor.fetchall()
            
            # Format dates to string
            for semester in semesters_raw:
                if semester['start_date']:
                    semester['start_date'] = semester['start_date'].strftime('%Y-%m-%d')
                if semester['end_date']:
                    semester['end_date'] = semester['end_date'].strftime('%Y-%m-%d')
            return semesters_raw
        
        calendar_data = handle_db_operation(operation)
        
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
            cursor = conn.cursor(cursor_factory=RealDictCursor) # Use RealDictCursor
            
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
            program, year, gender, count = row['program'], row['year_of_study'], row['gender'], row['student_count']
            total_students += count
            
            if program not in programs_stats:
                programs_stats[program] = {
                    "program": program,
                    "total_students": 0,
                    "by_year": {},
                    "by_gender": {"Male": 0, "Female": 0, "Other": 0} # Initialize all genders
                }
            
            programs_stats[program]["total_students"] += count
            
            if year not in programs_stats[program]["by_year"]:
                programs_stats[program]["by_year"][year] = 0
            programs_stats[program]["by_year"][year] += count
            
            # Ensure gender is handled even if None or unexpected
            gender_key = gender if gender in ["Male", "Female"] else "Other"
            programs_stats[program]["by_gender"][gender_key] += count
        
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
            cursor = conn.cursor(cursor_factory=RealDictCursor) # Use RealDictCursor
            
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
                base_query += " AND s.semester_name ILIKE %s"
                params.append(f"%{semester_name}%")
            if course_code:
                base_query += " AND c.course_code ILIKE %s"
                params.append(f"%{course_code}%")
            
            base_query += " GROUP BY g.grade, g.grade_point, c.course_code, c.course_title, s.semester_name"
            base_query += " ORDER BY c.course_code, g.grade_point DESC"
            
            cursor.execute(base_query, params)
            return cursor.fetchall()
        
        grade_data = handle_db_operation(operation)
        
        # Process data
        distribution = {}
        grade_summary = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0, "F": 0} # Initialize all possible grades
        
        for row in grade_data:
            grade, grade_point, count, course_code, course_title, semester = row['grade'], row['grade_point'], row['count'], row['course_code'], row['course_title'], row['semester_name']
            
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
            cursor = conn.cursor(cursor_factory=RealDictCursor) # Use RealDictCursor
            
            # Get student details
            cursor.execute("""
                SELECT student_id, index_number, full_name, dob, gender, 
                       contact_email, contact_phone, program, year_of_study
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
                ORDER BY s.academic_year, s.start_date, c.course_code
            """, (student_data['student_id'],))
            
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
                "index_number": student_data['index_number'],
                "full_name": student_data['full_name'],
                "date_of_birth": student_data['dob'].strftime('%Y-%m-%d') if student_data['dob'] else None,
                "gender": student_data['gender'],
                "email": student_data['contact_email'],
                "phone": student_data['contact_phone'],
                "program": student_data['program'],
                "year_of_study": student_data['year_of_study']
            },
            "academic_record": {},
            "summary": {
                "total_courses": 0,
                "total_credit_hours": 0,
                "cumulative_gpa": 0.0
            }
        }
        
        # Group by semester
        total_points = 0.0
        total_credits = 0
        
        for grade_row in grades_data:
            course_code = grade_row['course_code']
            course_title = grade_row['course_title']
            credit_hours = grade_row['credit_hours']
            score = grade_row['score']
            grade = grade_row['grade']
            grade_point = grade_row['grade_point']
            semester_name = grade_row['semester_name']
            academic_year = grade_row['academic_year']
            
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
                "score": float(score), # Ensure score is float
                "grade": grade,
                "grade_point": float(grade_point) # Ensure grade_point is float
            })
            
            transcript["academic_record"][semester_name]["semester_credits"] += credit_hours
            total_credits += credit_hours
            total_points += float(grade_point) * credit_hours # Ensure float multiplication
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
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get summary statistics
        stats = {}
        
        # Total students
        cursor.execute("SELECT COUNT(*) FROM student_profiles")
        stats['total_students'] = cursor.fetchone()['count']
        
        # Total courses
        cursor.execute("SELECT COUNT(*) FROM courses")
        stats['total_courses'] = cursor.fetchone()['count']
        
        # Total grades
        grade_query = "SELECT COUNT(*) as count FROM grades g JOIN semesters s ON g.semester_id = s.semester_id WHERE 1=1"
        params = []
        
        if semester:
            grade_query += " AND s.semester_name ILIKE %s"
            params.append(f"%{semester}%")
            
        if academic_year:
            grade_query += " AND s.academic_year ILIKE %s"
            params.append(f"%{academic_year}%")
            
        cursor.execute(grade_query, params)
        stats['total_grades'] = cursor.fetchone()['count']
        
        # Grade distribution
        dist_query = """
            SELECT g.grade, COUNT(*) as count 
            FROM grades g
            JOIN semesters s ON g.semester_id = s.semester_id
            WHERE 1=1
        """
        if semester:
            dist_query += " AND s.semester_name ILIKE %s"
            params.append(f"%{semester}%")
        if academic_year:
            dist_query += " AND s.academic_year ILIKE %s"
            params.append(f"%{academic_year}%")
        dist_query += " GROUP BY g.grade ORDER BY g.grade"
        
        cursor.execute(dist_query, params)
        grade_distribution_raw = cursor.fetchall()
        grade_distribution = {row['grade']: row['count'] for row in grade_distribution_raw}
        
        # Average GPA calculation
        gpa_query = """
            SELECT AVG(g.grade_point) as avg_gpa 
            FROM grades g
            JOIN semesters s ON g.semester_id = s.semester_id
            WHERE 1=1
        """
        
        if semester:
            gpa_query += " AND s.semester_name ILIKE %s"
            params.append(f"%{semester}%")
        if academic_year:
            gpa_query += " AND s.academic_year ILIKE %s"
            params.append(f"%{academic_year}%")
        
        cursor.execute(gpa_query, params)
        avg_gpa_result = cursor.fetchone()
        avg_gpa = round(avg_gpa_result['avg_gpa'], 2) if avg_gpa_result and avg_gpa_result['avg_gpa'] else 0.0
        
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
            all_records = fetch_all_records(conn)
            if all_records and all_records.get('students') and all_records.get('grades'):
                # Transform the data structure for the PDF report
                student_records = []
                students_dict = {s['student_id']: s for s in all_records['students']}
                
                # Group grades by student
                student_grades = {}
                for grade in all_records['grades']:
                    student_id = None
                    # Find student_id from index_number
                    for sid, student in students_dict.items():
                        if student['index_number'] == grade['index_number']:
                            student_id = sid
                            break
                    
                    if student_id:
                        if student_id not in student_grades:
                            student_grades[student_id] = []
                        student_grades[student_id].append({
                            'course_code': grade['course_code'],
                            'course_title': grade['course_title'],
                            'semester_name': grade['semester_name'],
                            'academic_year': grade['academic_year'],
                            'score': grade['score'],
                            'grade': grade['grade'],
                            'grade_point': grade['grade_point']
                        })
                
                # Create the expected structure
                for student_id, student_profile in students_dict.items():
                    student_record = {
                        'profile': student_profile,
                        'grades': student_grades.get(student_id, [])
                    }
                    student_records.append(student_record)
                
                pdf_path = export_summary_report_pdf(student_records, f"summary_report_{semester or 'all'}.pdf")
            else:
                # Create empty report if no data
                pdf_path = export_summary_report_pdf([], f"summary_report_{semester or 'all'}.pdf")
            report_data["pdf_path"] = pdf_path
        elif format == "txt":
            all_records = fetch_all_records(conn)
            if all_records and all_records.get('students') and all_records.get('grades'):
                # Transform the data structure for the TXT report
                student_records = []
                students_dict = {s['student_id']: s for s in all_records['students']}
                
                # Group grades by student
                student_grades = {}
                for grade in all_records['grades']:
                    student_id = None
                    # Find student_id from index_number
                    for sid, student in students_dict.items():
                        if student['index_number'] == grade['index_number']:
                            student_id = sid
                            break
                    
                    if student_id:
                        if student_id not in student_grades:
                            student_grades[student_id] = []
                        student_grades[student_id].append({
                            'course_code': grade['course_code'],
                            'course_title': grade['course_title'],
                            'semester_name': grade['semester_name'],
                            'academic_year': grade['academic_year'],
                            'score': grade['score'],
                            'grade': grade['grade'],
                            'grade_point': grade['grade_point']
                        })
                
                # Create the expected structure
                for student_id, student_profile in students_dict.items():
                    student_record = {
                        'profile': student_profile,
                        'grades': student_grades.get(student_id, [])
                    }
                    student_records.append(student_record)
                
                txt_path = export_summary_report_txt(student_records, f"summary_report_{semester or 'all'}.txt")
            else:
                # Create empty report if no data
                txt_path = export_summary_report_txt([], f"summary_report_{semester or 'all'}.txt")
            report_data["txt_path"] = txt_path
        elif format == "excel":
            all_records = fetch_all_records(conn)
            if all_records and all_records.get('students') and all_records.get('grades'):
                # Transform the data structure for the Excel report
                student_records = []
                students_dict = {s['student_id']: s for s in all_records['students']}
                
                # Group grades by student
                student_grades = {}
                for grade in all_records['grades']:
                    student_id = None
                    # Find student_id from index_number
                    for sid, student in students_dict.items():
                        if student['index_number'] == grade['index_number']:
                            student_id = sid
                            break
                    
                    if student_id:
                        if student_id not in student_grades:
                            student_grades[student_id] = []
                        student_grades[student_id].append({
                            'course_code': grade['course_code'],
                            'score': grade['score']
                        })
                
                # Create the expected structure
                for student_id, student_profile in students_dict.items():
                    student_record = {
                        'profile': {
                            'index_number': student_profile['index_number'],
                            'name': student_profile['full_name'],
                            'program': student_profile['program'],
                            'year_of_study': student_profile['year_of_study'],
                            'dob': str(student_profile['dob']) if student_profile['dob'] else '',
                            'gender': student_profile['gender'],
                            'contact_email': student_profile['contact_email']
                        },
                        'grades': student_grades.get(student_id, [])
                    }
                    student_records.append(student_record)
                
                excel_path = export_summary_report_excel(student_records, f"summary_report_{semester or 'all'}.xlsx")
            else:
                # Create empty report if no data
                excel_path = export_summary_report_excel([], f"summary_report_{semester or 'all'}.xlsx")
            report_data["excel_path"] = excel_path
        elif format == "csv":
            all_records = fetch_all_records(conn)
            if all_records and all_records.get('students') and all_records.get('grades'):
                # Transform the data structure for the CSV report
                student_records = []
                students_dict = {s['student_id']: s for s in all_records['students']}
                
                # Group grades by student
                student_grades = {}
                for grade in all_records['grades']:
                    student_id = None
                    # Find student_id from index_number
                    for sid, student in students_dict.items():
                        if student['index_number'] == grade['index_number']:
                            student_id = sid
                            break
                    
                    if student_id:
                        if student_id not in student_grades:
                            student_grades[student_id] = []
                        student_grades[student_id].append({
                            'course_code': grade['course_code'],
                            'score': grade['score']
                        })
                
                # Create the expected structure
                for student_id, student_profile in students_dict.items():
                    student_record = {
                        'profile': {
                            'index_number': student_profile['index_number'],
                            'name': student_profile['full_name'],
                            'program': student_profile['program'],
                            'year_of_study': student_profile['year_of_study'],
                            'dob': str(student_profile['dob']) if student_profile['dob'] else '',
                            'gender': student_profile['gender'],
                            'contact_email': student_profile['contact_email']
                        },
                        'grades': student_grades.get(student_id, [])
                    }
                    student_records.append(student_record)
                
                csv_path = export_summary_report_csv(student_records, f"summary_report_{semester or 'all'}.csv")
            else:
                # Create empty report if no data
                csv_path = export_summary_report_csv([], f"summary_report_{semester or 'all'}.csv")
            report_data["csv_path"] = csv_path
        
        return report_data
        
    except Exception as e:
        logger.error(f"Error generating comprehensive report: {str(e)}")
        return None

def get_dashboard_analytics(conn):
    """Get dashboard analytics data"""
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        analytics = {}
        
        # Recent activity (last 30 days simulation) - This needs real data or a more complex query
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
                "semester": row['semester_name'],
                "average_gpa": round(row['avg_gpa'], 2) if row['avg_gpa'] else 0.0,
                "total_grades": row['total_grades']
            })
        
        analytics['semester_performance'] = semester_performance
        
        # Top performing students
        cursor.execute("""
            SELECT sp.index_number, sp.full_name, AVG(g.grade_point) as avg_gpa, COUNT(g.grade_id) as total_courses
            FROM student_profiles sp
            JOIN grades g ON sp.student_id = g.student_id
            GROUP BY sp.index_number, sp.full_name
            HAVING COUNT(g.grade_id) >= 3 -- Only consider students with at least 3 grades
            ORDER BY avg_gpa DESC
            LIMIT 10
        """)
        
        top_students = []
        for row in cursor.fetchall():
            top_students.append({
                "index_number": row['index_number'],
                "full_name": row['full_name'],
                "average_gpa": round(row['avg_gpa'], 2),
                "total_courses": row['total_courses']
            })
        
        analytics['top_students'] = top_students
        
        # Course statistics
        cursor.execute("""
            SELECT c.course_code, c.course_title, AVG(g.score) as avg_score, COUNT(g.grade_id) as enrollments
            FROM courses c
            LEFT JOIN grades g ON c.course_id = g.course_id
            GROUP BY c.course_code, c.course_title
            ORDER BY enrollments DESC
        """)
        
        course_stats = []
        for row in cursor.fetchall():
            course_stats.append({
                "course_code": row['course_code'],
                "course_title": row['course_title'],
                "average_score": round(float(row['avg_score']), 2) if row['avg_score'] else 0.0,
                "total_enrollments": row['enrollments'] if row['enrollments'] else 0
            })
        
        analytics['course_statistics'] = course_stats
        
        return analytics
        
    except Exception as e:
        logger.error(f"Error getting dashboard analytics: {str(e)}")
        return {}

# =============================
# ASSESSMENT ENDPOINTS
# =============================

@app.get("/assessments", response_model=List[AssessmentOut])
async def list_assessments(course_code: Optional[str] = Query(None, description="Filter by course code"), current_user: dict = Depends(get_current_user)):
    conn = connect_to_db()
    try:
        rows = fetch_assessments(conn, course_code)
        return [AssessmentOut(**r) for r in rows]
    except Exception as e:
        logger.error(f"Error listing assessments: {e}")
        raise HTTPException(status_code=500, detail="Failed to list assessments")
    finally:
        if conn: conn.close()

@app.post("/assessments", response_model=APIResponse)
async def create_assessment_endpoint(payload: AssessmentCreate, current_user: dict = Depends(require_admin_role)):
    conn = connect_to_db()
    try:
        aid = create_assessment(conn, payload.course_code, payload.assessment_name, payload.max_score, payload.weight)
        if not aid:
            raise HTTPException(status_code=400, detail="Assessment create failed")
        # Return new list subset for convenience
        rows = fetch_assessments(conn, payload.course_code)
        return APIResponse(success=True, message="Assessment created", data={"assessment_id": aid, "assessments": rows})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating assessment: {e}")
        raise HTTPException(status_code=500, detail="Failed to create assessment")
    finally:
        if conn: conn.close()

@app.put("/assessments/{assessment_id}", response_model=APIResponse)
async def update_assessment_endpoint(assessment_id: int = Path(...), payload: Optional[AssessmentUpdate] = None, current_user: dict = Depends(require_admin_role)):
    conn = connect_to_db()
    try:
        ok = update_assessment(conn, assessment_id,
                               assessment_name=payload.assessment_name if payload else None,
                               max_score=payload.max_score if payload else None,
                               weight=payload.weight if payload else None)
        if not ok:
            raise HTTPException(status_code=404, detail="Assessment not found or no changes")
        return APIResponse(success=True, message="Assessment updated")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating assessment {assessment_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update assessment")
    finally:
        if conn: conn.close()

@app.delete("/assessments/{assessment_id}", response_model=APIResponse)
async def delete_assessment_endpoint(assessment_id: int = Path(...), current_user: dict = Depends(require_admin_role)):
    conn = connect_to_db()
    try:
        ok = delete_assessment(conn, assessment_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Assessment not found")
        return APIResponse(success=True, message="Assessment deleted")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting assessment {assessment_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete assessment")
    finally:
        if conn: conn.close()

# =============================
# NOTIFICATION ENDPOINTS
# =============================

@app.get("/notifications", response_model=List[UserNotificationOut])
async def list_notifications(
    unread_only: Optional[bool] = Query(False),
    limit: Optional[int] = Query(20, ge=1, le=50),
    before_id: Optional[int] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    conn = connect_to_db()
    try:
        results = fetch_user_notifications(conn, current_user.get('user_id'), unread_only=unread_only or False, limit=limit or 20, before_id=before_id)
        return [UserNotificationOut(**r) for r in results]
    except Exception as e:
        logger.error(f"Error listing notifications: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch notifications")
    finally:
        if conn: conn.close()

@app.get("/notifications/unread-count")
async def unread_count(current_user: dict = Depends(get_current_user)):
    conn = connect_to_db()
    try:
        count = count_unread_notifications(conn, current_user.get('user_id'))
        return {"unread": count}
    except Exception as e:
        logger.error(f"Error counting unread notifications: {e}")
        raise HTTPException(status_code=500, detail="Failed to count unread notifications")
    finally:
        if conn: conn.close()

@app.post("/notifications/{user_notification_id}/read")
async def mark_one_read(user_notification_id: int, current_user: dict = Depends(get_current_user)):
    conn = connect_to_db()
    try:
        success = mark_notification_read(conn, current_user.get('user_id'), user_notification_id)
        if success:
            try:
                await broadcaster.publish("notification.read", {"user_notification_id": user_notification_id, "user": current_user.get('username')})
            except Exception:
                logger.warning("Failed to publish notification.read event")
        return {"success": success}
    except Exception as e:
        logger.error(f"Error marking notification read: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark read")
    finally:
        if conn: conn.close()

@app.post("/notifications/read-all")
async def mark_all_read(current_user: dict = Depends(get_current_user)):
    conn = connect_to_db()
    try:
        changed = mark_all_notifications_read(conn, current_user.get('user_id'))
        if changed:
            try:
                await broadcaster.publish("notification.read_all", {"user": current_user.get('username'), "count": changed})
            except Exception:
                logger.warning("Failed to publish notification.read_all event")
        return {"updated": changed}
    except Exception as e:
        logger.error(f"Error marking all notifications read: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark all read")
    finally:
        if conn: conn.close()

@app.post("/admin/notifications", response_model=APIResponse)
async def create_notification_endpoint(payload: NotificationCreate, current_user: dict = Depends(require_admin_role)):
    conn = connect_to_db()
    try:
        nid = insert_notification(
            conn,
            payload.type,
            payload.title,
            payload.message,
            payload.severity or 'info',
            payload.audience or 'all',
            payload.target_user_id,
            None,
            None,
            payload.expires_at
        )
        if not nid:
            raise HTTPException(status_code=500, detail="Failed to create notification")
        user_ids = _expand_audience_user_ids(conn, payload.audience, payload.target_user_id, None)
        create_user_notification_links(conn, nid, user_ids)
        try:
            await broadcaster.publish("notification.new", {
                "notification_id": nid,
                "title": payload.title,
                "severity": payload.severity or 'info',
                "audience": payload.audience or 'all',
                "recipients": len(user_ids)
            })
        except Exception:
            logger.warning("Failed to publish notification.new event")
        return APIResponse(success=True, message="Notification created", data={"notification_id": nid, "recipients": len(user_ids)})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating notification: {e}")
        raise HTTPException(status_code=500, detail="Failed to create notification")
    finally:
        if conn: conn.close()

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

