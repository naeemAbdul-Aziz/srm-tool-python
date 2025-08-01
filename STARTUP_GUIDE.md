# SRM System Startup and Testing Guide

## Quick Start Instructions

### 1. Start the Backend API
Open PowerShell in the `backend` directory and run:
```powershell
cd c:\Users\naeemaziz\Desktop\srm-tool-python\backend
python main.py
```

The API should start on `http://localhost:8000`

### 2. Test Backend is Running
Open browser and go to: `http://localhost:8000/docs`
You should see the Swagger UI documentation.

### 3. Initialize Database (if needed)
In another PowerShell window:
```powershell
cd c:\Users\naeemaziz\Desktop\srm-tool-python\backend
python -c "from db import create_tables_if_not_exist; create_tables_if_not_exist(); print('Database initialized!')"
```

### 4. Create Test Users (if needed)
```powershell
python -c "
from auth import create_user, create_student_account
create_user('admin', 'admin123', 'admin')
create_student_account('student1', 'pass123', 'ST001', 'Test Student')
print('Test users created!')
"
```

### 5. Open Frontend
Open this file in your browser:
`file:///c:/Users/naeemaziz/Desktop/srm-tool-python/frontend/index.html`

### 6. Test Login
Try these credentials:
- **Admin**: username=`admin`, password=`admin123`
- **Student**: username=`student1`, password=`pass123`

## Debugging Steps

### If Login Fails:

1. **Check Browser Console**
   - Open DevTools (F12)
   - Look for errors in Console tab
   - Check Network tab for failed requests

2. **Verify Backend Connection**
   - Go to `http://localhost:8000/health` 
   - Should return: `{"message": "API is healthy"}`

3. **Test API Authentication**
   - Go to `http://localhost:8000/docs`
   - Click "Authorize" button
   - Enter admin/admin123
   - Try calling `/me` endpoint

4. **Check CORS**
   - If you see CORS errors, the backend CORS is configured to allow all origins
   - Make sure backend is running on port 8000

### Common Issues:

1. **Backend not running**: Start with `python main.py`
2. **Database not initialized**: Run the database initialization script
3. **No users created**: Create test users with the script above
4. **Port conflicts**: Make sure port 8000 is available

### Success Indicators:

✅ Backend responds to `http://localhost:8000/health`
✅ Swagger UI loads at `http://localhost:8000/docs`
✅ Frontend loads without console errors
✅ Login redirects to dashboard based on role
✅ Admin sees sidebar with Students, Courses, etc.
✅ Student sees profile dashboard

### Next Steps After Login Works:

1. **For Admin Dashboard**:
   - Test adding students via "Students" tab
   - Test adding courses via "Courses" tab
   - Test bulk upload functionality

2. **For Student Dashboard**:
   - View profile information
   - Check grades (if any exist)
   - Test password change functionality

## File Structure Reference:
```
backend/
  ├── main.py          # Start this to run the API
  ├── api.py           # API endpoints
  ├── db.py            # Database operations
  └── auth.py          # Authentication

frontend/
  ├── index.html       # Open this in browser
  ├── styles.css       # UI styling
  └── script.js        # Frontend logic
```
