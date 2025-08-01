# Student Result Management System - Enterprise Dashboard

## Overview

A professional, enterprise-grade web dashboard for managing student records, courses, grades, and academic administration. Features a clean, modern interface with real-time data integration through REST API endpoints.

## Features

### 🔐 Authentication
- Full-page login with branding
- HTTP Basic Authentication
- Session management with localStorage
- Automatic logout on session expiry

### 📊 Dashboard Overview
- Real-time statistics (students, courses, grades, semesters)
- Quick action cards
- Professional sidebar navigation
- Responsive design for all devices

### 👥 Student Management
- View all students in a searchable table
- Add new students with comprehensive forms
- Student profile viewing
- Real-time search functionality

### 📚 Course Management
- Course listing and details
- Add new courses
- Course code and credit hours tracking

### 📈 Grade Management
- Grade recording and viewing
- Score updates
- Academic performance tracking
- Semester-based organization

### 🗓️ Semester Management
- Academic year organization
- Semester creation and management
- Date range tracking

### 📄 Reports
- Academic performance reports
- Data export capabilities
- Statistical analysis

### ⚙️ System Administration
- Database initialization
- Sample data seeding
- Bulk data import via CSV
- System health monitoring

## Technical Stack

- **Frontend**: Vanilla HTML5, CSS3, JavaScript (ES6+)
- **Backend**: Python 3, FastAPI
- **Database**: PostgreSQL
- **Authentication**: HTTP Basic Auth
- **Styling**: Font Awesome icons, Google Fonts (Inter)

## Getting Started

### Prerequisites
- Python 3.8+
- PostgreSQL database
- Web browser (Chrome, Firefox, Safari, Edge)

### Installation

1. **Backend Setup**
   ```bash
   cd backend
   pip install -r requirements.txt
   python main.py
   ```

2. **Frontend Setup**
   ```bash
   cd frontend
   # Open index.html in your web browser
   # Or serve via local web server:
   python -m http.server 8080
   ```

3. **Database Setup**
   - Ensure PostgreSQL is running
   - Update database credentials in `backend/config.py`
   - Initialize the system through the dashboard

### Default Login
- **Username**: admin
- **Password**: admin123

3. Access the dashboard at `http://localhost:8080` (or your chosen port)

## 🔐 Login Credentials

Use your existing admin credentials from the backend system. The dashboard supports HTTP Basic Authentication that integrates with your FastAPI auth system.

**Default credentials** (if using seeded data):
- Username: `admin`
- Password: `admin123` (or whatever you've configured)

## 📱 Features Walkthrough

### Adding Students
1. Go to **Students & Courses** tab
2. Fill out the "Add Student" form with:
   - Index Number (format: ug12345)
   - Full Name
   - Optional: Date of Birth, Gender, Email, Phone, Program, Year
3. Click "Add Student"

### Adding Courses
1. In **Students & Courses** tab
2. Use the "Add Course" form:
   - Course Code (e.g., UGCS101)
   - Course Title
   - Credit Hours
3. Click "Add Course"

### Managing Grades
1. Go to **Grades & Semesters** tab
2. Add grades using student index, course code, semester, and score
3. Update existing scores using the "Update Student Score" section

### Bulk Upload
1. Navigate to **Management** tab
2. Use the "Bulk Upload Students" section
3. Upload a CSV file with columns: `index_number,full_name,dob,gender,contact_email,phone,program,year_of_study`
4. File will be processed and students added automatically

### Student Profile Viewer
1. In **Management** tab
2. Enter a student index number in "Student Profile Viewer"
3. Click "View Profile" to see complete student information

## 🛠 Configuration

### API Base URL
The dashboard is configured to connect to `http://localhost:8000` by default. To change this:

1. Open `script.js`
2. Modify the `baseURL` in the constructor:
   ```javascript
   constructor() {
       this.baseURL = 'http://your-api-url:port'; // Change this
       // ...
   }
   ```

### Authentication
The dashboard uses HTTP Basic Authentication. Credentials are stored in localStorage for session persistence.

## 📊 API Endpoints Used

The dashboard integrates with these API endpoints:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Authentication & health check |
| `/admin/students` | GET | Fetch all students |
| `/admin/students` | POST | Create student |
| `/admin/student/{id}` | GET | Get student by ID |
| `/admin/student/{id}` | DELETE | Delete student |
| `/admin/courses` | GET/POST | Manage courses |
| `/admin/semesters` | GET/POST | Manage semesters |
| `/admin/grades` | POST | Add grades |
| `/admin/update-score` | PUT | Update student scores |
| `/admin/bulk-upload` | POST | Bulk import students |
| `/admin/seed-comprehensive` | POST | Seed database |
| `/initialize` | POST | Initialize system |

## 🎨 Design Features

- **Clean & Minimal**: Inspired by modern dashboard designs
- **Responsive**: Works on desktop, tablet, and mobile devices
- **Accessible**: Proper ARIA labels and keyboard navigation
- **Fast**: Optimized API calls with loading states
- **User-Friendly**: Clear notifications and error handling

## 🔧 Customization

### Styling
Modify `styles.css` to customize:
- Color scheme (update CSS variables)
- Layout and spacing
- Component styling

### Functionality
Extend `script.js` to add:
- Additional API endpoints
- Custom form validations
- Enhanced charts and analytics
- Export functionality

## 🚨 Troubleshooting

### Authentication Issues
- Verify your API is running on the correct port
- Check that CORS is properly configured in your FastAPI backend
- Ensure your credentials are correct

### API Connection Problems
- Check the `baseURL` in `script.js`
- Verify your FastAPI server is accessible
- Check browser console for detailed error messages

### Data Not Loading
- Ensure you have proper admin permissions
- Check that the database is initialized and seeded
- Verify API endpoints are responding correctly

## 📝 Browser Compatibility

- Chrome/Chromium 80+
- Firefox 75+
- Safari 13+
- Edge 80+

## 🤝 Support

For issues related to:
- **Frontend Dashboard**: Check browser console for errors
- **API Integration**: Verify backend is running and endpoints are accessible
- **Authentication**: Ensure credentials and backend auth configuration are correct
