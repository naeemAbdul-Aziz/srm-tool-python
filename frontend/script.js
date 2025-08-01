// Enterprise Student Result Management System - Frontend JavaScript
// Professional grade system with proper navigation and accurate data

class SRMDashboard {
    constructor() {
        this.baseURL = 'http://localhost:8000'; // Adjust this to your API URL
        this.authToken = null;
        this.currentUser = null;
        this.currentPage = 'overview';
        this.init();
        
        // Add debugging
        console.log('SRM Dashboard initialized');
        console.log('Base URL:', this.baseURL);
    }

    init() {
        this.attachEventListeners();
        this.checkAuthState();
    }

    // Authentication and Navigation Methods
    attachEventListeners() {
        // Login form
        document.getElementById('loginForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleLogin();
        });

        // Logout buttons (both admin and student)
        document.getElementById('logoutBtn').addEventListener('click', () => {
            this.handleLogout();
        });
        
        document.getElementById('studentLogoutBtn').addEventListener('click', () => {
            this.handleLogout();
        });

        // Admin Navigation
        document.querySelectorAll('#dashboard .nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const page = e.currentTarget.getAttribute('data-page');
                this.navigateToPage(page);
            });
        });

        // Student Navigation
        document.querySelectorAll('#studentDashboard .nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const page = e.currentTarget.getAttribute('data-page');
                this.navigateToStudentPage(page);
            });
        });

        // Form submissions
        this.attachFormListeners();
        
        // File upload
        this.attachFileUploadListeners();

        // Modal handling
        this.attachModalListeners();
    }

    attachFormListeners() {
        // Add Student Form
        const addStudentForm = document.getElementById('addStudentForm');
        if (addStudentForm) {
            addStudentForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleAddStudent();
            });
        }
    }

    attachModalListeners() {
        // Modal overlay click to close
        const modalOverlay = document.getElementById('modalOverlay');
        if (modalOverlay) {
            modalOverlay.addEventListener('click', (e) => {
                if (e.target === modalOverlay) {
                    this.closeModal();
                }
            });
        }
    }

    attachFileUploadListeners() {
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('bulkUploadFile');

        if (uploadArea && fileInput) {
            // Drag and drop functionality
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('dragover');
            });

            uploadArea.addEventListener('dragleave', () => {
                uploadArea.classList.remove('dragover');
            });

            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    this.handleFileUpload(files[0]);
                }
            });

            uploadArea.addEventListener('click', () => {
                fileInput.click();
            });

            // File input change
            fileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    this.handleFileUpload(e.target.files[0]);
                }
            });
        }
    }

    checkAuthState() {
        const token = localStorage.getItem('srmToken');
        const user = localStorage.getItem('srmUser');
        
        if (token && user) {
            this.authToken = token;
            this.currentUser = JSON.parse(user);
            
            // Route to appropriate dashboard based on stored role
            if (this.currentUser.role === 'admin') {
                this.showAdminDashboard();
            } else if (this.currentUser.role === 'student') {
                this.showStudentDashboard();
            } else {
                this.showLogin();
            }
        } else {
            this.showLogin();
        }
    }

    async handleLogin() {
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const errorDiv = document.getElementById('loginError');
        
        // Clear previous errors
        errorDiv.textContent = '';

        try {
            this.showLoading(true);
            
            const credentials = btoa(`${username}:${password}`);
            
            // Direct authentication via /me endpoint
            const response = await fetch(`${this.baseURL}/me`, {
                method: 'GET',
                headers: {
                    'Authorization': `Basic ${credentials}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                if (response.status === 401) {
                    throw new Error('Invalid username or password');
                } else if (response.status === 403) {
                    throw new Error('Access denied');
                } else {
                    throw new Error('Server error. Please try again.');
                }
            }

            const userInfoData = await response.json();
            
            if (!userInfoData.success) {
                throw new Error(userInfoData.message || 'Authentication failed');
            }

            const userData = userInfoData.data;
            this.handleSuccessfulLogin(credentials, userData);
            
        } catch (error) {
            console.error('Login error details:', {
                message: error.message,
                stack: error.stack,
                error: error
            });
            
            let errorMessage = 'Login failed';
            if (error.message.includes('fetch') || error.message.includes('NetworkError')) {
                errorMessage = 'Cannot connect to server. Make sure the backend is running on port 8000.';
            } else {
                errorMessage = error.message || 'Unknown error occurred';
            }
            
            errorDiv.textContent = errorMessage;
            this.showNotification('Login failed: ' + errorMessage, 'error');
        } finally {
            this.showLoading(false);
        }
    }

    handleSuccessfulLogin(credentials, userData) {
        // Store auth data
        this.authToken = credentials;
        this.currentUser = {
            username: userData.username,
            role: userData.role
        };
        
        localStorage.setItem('srmToken', credentials);
        localStorage.setItem('srmUser', JSON.stringify(this.currentUser));
        
        // Route to appropriate dashboard based on role
        if (userData.role === 'admin') {
            this.showAdminDashboard();
        } else if (userData.role === 'student') {
            this.showStudentDashboard();
        } else {
            throw new Error('Unknown user role: ' + userData.role);
        }
        
        this.showNotification('Login successful!', 'success');
    }

    handleLogout() {
        localStorage.removeItem('srmToken');
        localStorage.removeItem('srmUser');
        this.authToken = null;
        this.currentUser = null;
        this.showLogin();
        this.showNotification('Logged out successfully', 'info');
    }

    showLogin() {
        document.getElementById('loginPage').classList.add('active');
        document.getElementById('dashboard').classList.add('hidden');
        document.getElementById('studentDashboard').classList.add('hidden');
    }

    showAdminDashboard() {
        document.getElementById('loginPage').classList.remove('active');
        document.getElementById('dashboard').classList.remove('hidden');
        document.getElementById('studentDashboard').classList.add('hidden');
        document.getElementById('currentUser').textContent = this.currentUser.username;
        this.navigateToPage('overview');
    }

    showStudentDashboard() {
        document.getElementById('loginPage').classList.remove('active');
        document.getElementById('dashboard').classList.add('hidden');
        document.getElementById('studentDashboard').classList.remove('hidden');
        document.getElementById('currentStudent').textContent = this.currentUser.username;
        this.navigateToStudentPage('student-overview');
    }

    // Legacy method for backward compatibility
    showDashboard() {
        this.showAdminDashboard();
    }

    // API Helper Methods
    async apiRequest(endpoint, method = 'GET', data = null) {
        const url = `${this.baseURL}${endpoint}`;
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            }
        };

        // Add authentication header if we have a token
        if (this.authToken) {
            options.headers['Authorization'] = `Basic ${this.authToken}`;
        }

        // Add request body for POST/PUT requests
        if (data && (method === 'POST' || method === 'PUT')) {
            options.body = JSON.stringify(data);
        }

        try {
            const response = await fetch(url, options);
            
            // Handle authentication errors
            if (response.status === 401) {
                this.handleLogout(); // Force logout on auth failure
                throw new Error('Authentication required');
            }
            
            if (!response.ok) {
                throw new Error(`API request failed: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API request error:', error);
            throw error;
        }
    }

    // Navigation Methods
    navigateToPage(pageName) {
        // Update active navigation (admin dashboard)
        document.querySelectorAll('#dashboard .nav-item').forEach(item => {
            item.classList.remove('active');
        });
        const navItem = document.querySelector(`#dashboard [data-page="${pageName}"]`);
        if (navItem) {
            navItem.classList.add('active');
        }

        // Update page content (admin dashboard)
        document.querySelectorAll('#dashboard .page').forEach(page => {
            page.classList.remove('active');
        });
        const pageElement = document.getElementById(pageName);
        if (pageElement) {
            pageElement.classList.add('active');
        }

        // Update page title and breadcrumb
        this.updatePageHeader(pageName);

        // Load page-specific data
        this.loadPageData(pageName);

        this.currentPage = pageName;
    }

    navigateToStudentPage(pageName) {
        // Update active navigation (student dashboard)
        document.querySelectorAll('#studentDashboard .nav-item').forEach(item => {
            item.classList.remove('active');
        });
        const navItem = document.querySelector(`#studentDashboard [data-page="${pageName}"]`);
        if (navItem) {
            navItem.classList.add('active');
        }

        // Update page content (student dashboard)
        document.querySelectorAll('#studentDashboard .page').forEach(page => {
            page.classList.remove('active');
        });
        const pageElement = document.getElementById(pageName);
        if (pageElement) {
            pageElement.classList.add('active');
        }

        // Update student page title and breadcrumb
        this.updateStudentPageHeader(pageName);

        // Load student page-specific data
        this.loadStudentPageData(pageName);

        this.currentPage = pageName;
    }

    updatePageHeader(pageName) {
        const titles = {
            'overview': 'Overview',
            'students': 'Students',
            'courses': 'Courses',
            'grades': 'Grades',
            'semesters': 'Semesters',
            'reports': 'Reports',
            'system': 'System'
        };

        document.getElementById('pageTitle').textContent = titles[pageName] || pageName;
        document.getElementById('breadcrumbPath').textContent = `Dashboard / ${titles[pageName] || pageName}`;
    }

    updateStudentPageHeader(pageName) {
        const titles = {
            'student-overview': 'My Dashboard',
            'student-profile': 'My Profile',
            'student-grades': 'My Grades',
            'student-gpa': 'GPA',
            'student-courses': 'My Courses'
        };

        document.getElementById('studentPageTitle').textContent = titles[pageName] || pageName;
        document.getElementById('studentBreadcrumbPath').textContent = `Student Portal / ${titles[pageName] || pageName}`;
    }

    // API Communication Methods
    async makeRequest(endpoint, options = {}) {
        try {
            const headers = {
                'Content-Type': 'application/json',
                ...options.headers
            };

            if (this.authToken) {
                headers['Authorization'] = `Basic ${this.authToken}`;
            }

            const response = await fetch(`${this.baseURL}${endpoint}`, {
                ...options,
                headers
            });

            if (!response.ok) {
                if (response.status === 401) {
                    this.handleLogout();
                    throw new Error('Session expired');
                }
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API Request Error:', error);
            throw error;
        }
    }

    // Data Loading Methods
    async loadPageData(pageName) {
        try {
            this.showLoading(true);
            
            switch (pageName) {
                case 'overview':
                    await this.loadOverviewData();
                    break;
                case 'students':
                    await this.loadStudents();
                    break;
                case 'courses':
                    await this.loadCourses();
                    break;
                case 'grades':
                    await this.loadGrades();
                    break;
                case 'semesters':
                    await this.loadSemesters();
                    break;
            }
        } catch (error) {
            console.error('Error loading page data:', error);
            this.showNotification('Error loading data', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    async loadStudentPageData(pageName) {
        try {
            this.showLoading(true);
            
            switch (pageName) {
                case 'student-overview':
                    await this.loadStudentOverview();
                    break;
                case 'student-profile':
                    await this.loadStudentProfile();
                    break;
                case 'student-grades':
                    await this.loadStudentGrades();
                    break;
                case 'student-gpa':
                    await this.loadStudentGPA();
                    break;
                case 'student-courses':
                    await this.loadStudentCourses();
                    break;
            }
        } catch (error) {
            console.error('Error loading student page data:', error);
            this.showNotification('Error loading data', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    async loadOverviewData() {
        try {
            // Load actual statistics from API
            const [studentsResponse, coursesResponse, semestersResponse] = await Promise.allSettled([
                this.makeRequest('/admin/students'),
                this.makeRequest('/admin/courses'),
                this.makeRequest('/admin/semesters')
            ]);

            // Update statistics with actual data
            const totalStudents = studentsResponse.status === 'fulfilled' ? 
                (studentsResponse.value.data?.length || 0) : 0;
            const totalCourses = coursesResponse.status === 'fulfilled' ? 
                (coursesResponse.value.data?.length || 0) : 0;
            const totalSemesters = semestersResponse.status === 'fulfilled' ? 
                (semestersResponse.value.data?.length || 0) : 0;

            document.getElementById('totalStudents').textContent = totalStudents;
            document.getElementById('totalCourses').textContent = totalCourses;
            document.getElementById('totalSemesters').textContent = totalSemesters;

            // Load grades count
            try {
                const gradesResponse = await this.makeRequest('/admin/grades');
                const totalGrades = gradesResponse.data?.length || 0;
                document.getElementById('totalGrades').textContent = totalGrades;
            } catch (error) {
                document.getElementById('totalGrades').textContent = '0';
            }

        } catch (error) {
            console.error('Error loading overview data:', error);
            // Set fallback values
            document.getElementById('totalStudents').textContent = '0';
            document.getElementById('totalCourses').textContent = '0';
            document.getElementById('totalSemesters').textContent = '0';
            document.getElementById('totalGrades').textContent = '0';
        }
    }

    async loadStudents(searchTerm = '') {
        try {
            const endpoint = searchTerm ? 
                `/admin/students/search?name=${encodeURIComponent(searchTerm)}` :
                '/admin/students';
            
            const response = await this.makeRequest(endpoint);
            this.displayStudentsTable(response.data || []);
        } catch (error) {
            console.error('Error loading students:', error);
            this.displayStudentsTable([]);
        }
    }

    async loadCourses() {
        try {
            const response = await this.makeRequest('/admin/courses');
            this.displayCoursesTable(response.data || []);
        } catch (error) {
            console.error('Error loading courses:', error);
            this.displayCoursesTable([]);
        }
    }

    async loadGrades() {
        try {
            const response = await this.makeRequest('/admin/grades');
            this.displayGradesTable(response.data || []);
        } catch (error) {
            console.error('Error loading grades:', error);
            this.displayGradesTable([]);
        }
    }

    async loadSemesters() {
        try {
            const response = await this.makeRequest('/admin/semesters');
            this.displaySemestersTable(response.data || []);
        } catch (error) {
            console.error('Error loading semesters:', error);
            this.displaySemestersTable([]);
        }
    }

    // Table Display Methods
    displayStudentsTable(students) {
        const tableContainer = document.getElementById('studentsTable');
        
        if (!students.length) {
            tableContainer.innerHTML = '<div class="empty-state"><p>No students found.</p></div>';
            return;
        }

        const table = `
            <table>
                <thead>
                    <tr>
                        <th>Index Number</th>
                        <th>Full Name</th>
                        <th>Program</th>
                        <th>Year</th>
                        <th>Email</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${students.map(student => `
                        <tr>
                            <td>${student.index_number || 'N/A'}</td>
                            <td>${student.full_name || 'N/A'}</td>
                            <td>${student.program || 'N/A'}</td>
                            <td>${student.year_of_study || 'N/A'}</td>
                            <td>${student.contact_email || 'N/A'}</td>
                            <td>
                                <button class="btn-info btn-sm" onclick="dashboard.viewStudentProfile('${student.index_number}')">
                                    View
                                </button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        
        tableContainer.innerHTML = table;
    }

    displayCoursesTable(courses) {
        const tableContainer = document.getElementById('coursesTable');
        
        if (!courses.length) {
            tableContainer.innerHTML = '<div class="empty-state"><p>No courses found.</p></div>';
            return;
        }

        const table = `
            <table>
                <thead>
                    <tr>
                        <th>Course Code</th>
                        <th>Course Title</th>
                        <th>Credit Hours</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${courses.map(course => `
                        <tr>
                            <td>${course.course_code || 'N/A'}</td>
                            <td>${course.course_title || 'N/A'}</td>
                            <td>${course.credit_hours || 'N/A'}</td>
                            <td>
                                <button class="btn-warning btn-sm">Edit</button>
                                <button class="btn-error btn-sm">Delete</button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        
        tableContainer.innerHTML = table;
    }

    displayGradesTable(grades) {
        const tableContainer = document.getElementById('gradesTable');
        
        if (!grades.length) {
            tableContainer.innerHTML = '<div class="empty-state"><p>No grades found.</p></div>';
            return;
        }

        const table = `
            <table>
                <thead>
                    <tr>
                        <th>Student</th>
                        <th>Course</th>
                        <th>Semester</th>
                        <th>Score</th>
                        <th>Grade</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${grades.map(grade => `
                        <tr>
                            <td>${grade.student_index || 'N/A'}</td>
                            <td>${grade.course_code || 'N/A'}</td>
                            <td>${grade.semester_name || 'N/A'}</td>
                            <td>${grade.score || 'N/A'}</td>
                            <td>${grade.letter_grade || 'N/A'}</td>
                            <td>
                                <button class="btn-warning btn-sm">Edit</button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        
        tableContainer.innerHTML = table;
    }

    displaySemestersTable(semesters) {
        const tableContainer = document.getElementById('semestersTable');
        
        if (!semesters.length) {
            tableContainer.innerHTML = '<div class="empty-state"><p>No semesters found.</p></div>';
            return;
        }

        const table = `
            <table>
                <thead>
                    <tr>
                        <th>Semester Name</th>
                        <th>Academic Year</th>
                        <th>Start Date</th>
                        <th>End Date</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${semesters.map(semester => `
                        <tr>
                            <td>${semester.semester_name || 'N/A'}</td>
                            <td>${semester.academic_year || 'N/A'}</td>
                            <td>${semester.start_date || 'N/A'}</td>
                            <td>${semester.end_date || 'N/A'}</td>
                            <td>
                                <button class="btn-warning btn-sm">Edit</button>
                                <button class="btn-error btn-sm">Delete</button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        
        tableContainer.innerHTML = table;
    }

    // Student Data Loading Methods
    async loadStudentOverview() {
        try {
            // Load student overview data
            const [profileResponse, gradesResponse, gpaResponse] = await Promise.allSettled([
                this.makeRequest('/student/profile'),
                this.makeRequest('/student/grades'),
                this.makeRequest('/student/gpa')
            ]);

            // Update student statistics
            if (profileResponse.status === 'fulfilled') {
                // Display basic profile info
            }

            if (gradesResponse.status === 'fulfilled') {
                const grades = gradesResponse.value.data || [];
                const totalCourses = new Set(grades.map(g => g.course_code)).size;
                document.getElementById('studentTotalCourses').textContent = totalCourses;
                
                // Show recent grades
                this.displayStudentRecentGrades(grades.slice(0, 5));
            } else {
                document.getElementById('studentTotalCourses').textContent = '0';
            }

            if (gpaResponse.status === 'fulfilled') {
                const gpaData = gpaResponse.value.data;
                document.getElementById('studentCurrentGPA').textContent = 
                    gpaData?.overall_gpa?.toFixed(2) || 'N/A';
                document.getElementById('studentTotalCredits').textContent = 
                    gpaData?.total_credits || '0';
            } else {
                document.getElementById('studentCurrentGPA').textContent = 'N/A';
                document.getElementById('studentTotalCredits').textContent = '0';
            }

            // Set current semester (placeholder)
            document.getElementById('studentCurrentSemester').textContent = 'Current';

        } catch (error) {
            console.error('Error loading student overview:', error);
            // Set fallback values
            document.getElementById('studentTotalCourses').textContent = '0';
            document.getElementById('studentCurrentGPA').textContent = 'N/A';
            document.getElementById('studentTotalCredits').textContent = '0';
            document.getElementById('studentCurrentSemester').textContent = 'N/A';
        }
    }

    async loadStudentProfile() {
        try {
            const response = await this.makeRequest('/student/profile');
            this.displayStudentProfileData(response.data);
        } catch (error) {
            console.error('Error loading student profile:', error);
            this.displayStudentProfileData(null);
        }
    }

    async loadStudentGrades() {
        try {
            const response = await this.makeRequest('/student/grades');
            this.displayStudentGradesTable(response.data || []);
        } catch (error) {
            console.error('Error loading student grades:', error);
            this.displayStudentGradesTable([]);
        }
    }

    async loadStudentGPA() {
        try {
            const response = await this.makeRequest('/student/gpa');
            this.displayStudentGPAData(response.data);
        } catch (error) {
            console.error('Error loading student GPA:', error);
            this.displayStudentGPAData(null);
        }
    }

    async loadStudentCourses() {
        try {
            const response = await this.makeRequest('/student/grades');
            // Extract unique courses from grades
            const grades = response.data || [];
            const courses = [];
            const courseSet = new Set();
            
            grades.forEach(grade => {
                if (!courseSet.has(grade.course_code)) {
                    courseSet.add(grade.course_code);
                    courses.push({
                        course_code: grade.course_code,
                        course_title: grade.course_title || 'N/A',
                        semester: grade.semester_name || 'N/A',
                        grade: grade.letter_grade || 'N/A'
                    });
                }
            });
            
            this.displayStudentCoursesTable(courses);
        } catch (error) {
            console.error('Error loading student courses:', error);
            this.displayStudentCoursesTable([]);
        }
    }

    // Student Display Methods
    displayStudentRecentGrades(grades) {
        const container = document.getElementById('studentRecentGrades');
        
        if (!grades.length) {
            container.innerHTML = '<div class="empty-state"><p>No recent grades available.</p></div>';
            return;
        }

        const table = `
            <table>
                <thead>
                    <tr>
                        <th>Course</th>
                        <th>Score</th>
                        <th>Grade</th>
                        <th>Semester</th>
                    </tr>
                </thead>
                <tbody>
                    ${grades.map(grade => `
                        <tr>
                            <td>${grade.course_code || 'N/A'}</td>
                            <td>${grade.score || 'N/A'}</td>
                            <td>${grade.letter_grade || 'N/A'}</td>
                            <td>${grade.semester_name || 'N/A'}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        
        container.innerHTML = table;
    }

    displayStudentProfileData(profile) {
        const container = document.getElementById('studentProfileData');
        
        if (!profile) {
            container.innerHTML = '<div class="empty-state"><p>Profile data not available.</p></div>';
            return;
        }

        container.innerHTML = `
            <div class="profile-grid">
                <div class="profile-item">
                    <label>Index Number:</label>
                    <span>${profile.index_number || 'N/A'}</span>
                </div>
                <div class="profile-item">
                    <label>Full Name:</label>
                    <span>${profile.full_name || 'N/A'}</span>
                </div>
                <div class="profile-item">
                    <label>Date of Birth:</label>
                    <span>${profile.dob || 'N/A'}</span>
                </div>
                <div class="profile-item">
                    <label>Gender:</label>
                    <span>${profile.gender || 'N/A'}</span>
                </div>
                <div class="profile-item">
                    <label>Email:</label>
                    <span>${profile.contact_email || 'N/A'}</span>
                </div>
                <div class="profile-item">
                    <label>Phone:</label>
                    <span>${profile.phone || 'N/A'}</span>
                </div>
                <div class="profile-item">
                    <label>Program:</label>
                    <span>${profile.program || 'N/A'}</span>
                </div>
                <div class="profile-item">
                    <label>Year of Study:</label>
                    <span>${profile.year_of_study || 'N/A'}</span>
                </div>
            </div>
        `;
    }

    displayStudentGradesTable(grades) {
        const container = document.getElementById('studentGradesTable');
        
        if (!grades.length) {
            container.innerHTML = '<div class="empty-state"><p>No grades available.</p></div>';
            return;
        }

        const table = `
            <table>
                <thead>
                    <tr>
                        <th>Course Code</th>
                        <th>Course Title</th>
                        <th>Semester</th>
                        <th>Score</th>
                        <th>Grade</th>
                        <th>Credit Hours</th>
                    </tr>
                </thead>
                <tbody>
                    ${grades.map(grade => `
                        <tr>
                            <td>${grade.course_code || 'N/A'}</td>
                            <td>${grade.course_title || 'N/A'}</td>
                            <td>${grade.semester_name || 'N/A'}</td>
                            <td>${grade.score || 'N/A'}</td>
                            <td>${grade.letter_grade || 'N/A'}</td>
                            <td>${grade.credit_hours || 'N/A'}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        
        container.innerHTML = table;
    }

    displayStudentGPAData(gpaData) {
        const container = document.getElementById('studentGPAData');
        
        if (!gpaData) {
            container.innerHTML = '<div class="empty-state"><p>GPA data not available.</p></div>';
            return;
        }

        container.innerHTML = `
            <div class="gpa-summary">
                <div class="gpa-card">
                    <h3>Overall GPA</h3>
                    <div class="gpa-value">${gpaData.overall_gpa?.toFixed(2) || 'N/A'}</div>
                </div>
                <div class="gpa-card">
                    <h3>Total Credits</h3>
                    <div class="gpa-value">${gpaData.total_credits || '0'}</div>
                </div>
                <div class="gpa-card">
                    <h3>Completed Courses</h3>
                    <div class="gpa-value">${gpaData.total_courses || '0'}</div>
                </div>
            </div>
        `;
    }

    displayStudentCoursesTable(courses) {
        const container = document.getElementById('studentCoursesTable');
        
        if (!courses.length) {
            container.innerHTML = '<div class="empty-state"><p>No courses available.</p></div>';
            return;
        }

        const table = `
            <table>
                <thead>
                    <tr>
                        <th>Course Code</th>
                        <th>Course Title</th>
                        <th>Semester</th>
                        <th>Grade</th>
                    </tr>
                </thead>
                <tbody>
                    ${courses.map(course => `
                        <tr>
                            <td>${course.course_code || 'N/A'}</td>
                            <td>${course.course_title || 'N/A'}</td>
                            <td>${course.semester || 'N/A'}</td>
                            <td>${course.grade || 'N/A'}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        
        container.innerHTML = table;
    }

    // Modal Methods
    showModal(modalId) {
        document.getElementById('modalOverlay').classList.add('active');
        document.getElementById(modalId).style.display = 'block';
    }

    closeModal() {
        document.getElementById('modalOverlay').classList.remove('active');
        document.querySelectorAll('.modal').forEach(modal => {
            modal.style.display = 'none';
        });
    }

    // Form Handler Methods
    async handleAddStudent() {
        try {
            this.showLoading(true);
            
            const studentData = {
                index_number: document.getElementById('studentIndexNumber').value,
                full_name: document.getElementById('studentFullName').value,
                dob: document.getElementById('studentDOB').value || null,
                gender: document.getElementById('studentGender').value || null,
                contact_email: document.getElementById('studentEmail').value || null,
                phone: document.getElementById('studentPhone').value || null,
                program: document.getElementById('studentProgram').value || null,
                year_of_study: parseInt(document.getElementById('studentYear').value) || null
            };

            const response = await this.makeRequest('/admin/students', {
                method: 'POST',
                body: JSON.stringify(studentData)
            });

            this.showNotification('Student added successfully!', 'success');
            this.closeModal();
            document.getElementById('addStudentForm').reset();
            
            // Refresh current page data
            if (this.currentPage === 'students') {
                this.loadStudents();
            }
            if (this.currentPage === 'overview') {
                this.loadOverviewData();
            }
        } catch (error) {
            console.error('Error adding student:', error);
            this.showNotification(`Error adding student: ${error.message}`, 'error');
        } finally {
            this.showLoading(false);
        }
    }

    // File Upload Handler
    async handleFileUpload(file) {
        try {
            if (!file.name.endsWith('.csv')) {
                throw new Error('Please upload a CSV file');
            }

            this.showLoading(true);
            
            const text = await file.text();
            const lines = text.split('\n').filter(line => line.trim());
            const headers = lines[0].split(',').map(h => h.trim());
            
            const data = lines.slice(1).map(line => {
                const values = line.split(',').map(v => v.trim());
                const obj = {};
                headers.forEach((header, index) => {
                    obj[header] = values[index] || '';
                });
                return obj;
            });

            // Upload to server
            const response = await this.makeRequest('/admin/bulk-upload', {
                method: 'POST',
                body: JSON.stringify({
                    semester_name: 'Current Semester',
                    file_data: data
                })
            });

            this.showNotification(`Bulk upload successful! ${data.length} records processed.`, 'success');
            
            // Refresh data
            this.loadOverviewData();
            if (this.currentPage === 'students') {
                this.loadStudents();
            }
        } catch (error) {
            console.error('Error uploading file:', error);
            this.showNotification(`Error uploading file: ${error.message}`, 'error');
        } finally {
            this.showLoading(false);
        }
    }

    // System Control Methods
    async seedDatabase() {
        try {
            if (!confirm('This will seed the database with sample data. Continue?')) {
                return;
            }

            this.showLoading(true);
            const response = await this.makeRequest('/admin/seed-comprehensive?num_students=50', {
                method: 'POST'
            });

            this.showNotification('Database seeded successfully!', 'success');
            this.loadOverviewData(); // Refresh overview data
        } catch (error) {
            console.error('Error seeding database:', error);
            this.showNotification(`Error seeding database: ${error.message}`, 'error');
        } finally {
            this.showLoading(false);
        }
    }

    async initializeSystem() {
        try {
            if (!confirm('This will initialize the database tables. Continue?')) {
                return;
            }

            this.showLoading(true);
            const response = await this.makeRequest('/initialize', {
                method: 'POST'
            });

            this.showNotification('System initialized successfully!', 'success');
        } catch (error) {
            console.error('Error initializing system:', error);
            this.showNotification(`Error initializing system: ${error.message}`, 'error');
        } finally {
            this.showLoading(false);
        }
    }

    // UI Helper Methods
    showLoading(show) {
        const overlay = document.getElementById('loadingOverlay');
        if (show) {
            overlay.classList.remove('hidden');
        } else {
            overlay.classList.add('hidden');
        }
    }

    showNotification(message, type = 'info') {
        const notifications = document.getElementById('notifications');
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        // Add click to dismiss
        notification.addEventListener('click', () => {
            notification.remove();
        });
        
        notifications.appendChild(notification);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }
}

// Global Functions
function navigateToPage(pageName) {
    if (window.dashboard) {
        window.dashboard.navigateToPage(pageName);
    }
}

function showAddStudentForm() {
    if (window.dashboard) {
        window.dashboard.showModal('addStudentModal');
    }
}

function showBulkImport() {
    navigateToPage('system');
}

function initializeSystem() {
    if (window.dashboard) {
        window.dashboard.initializeSystem();
    }
}

function seedDatabase() {
    if (window.dashboard) {
        window.dashboard.seedDatabase();
    }
}

function closeModal() {
    if (window.dashboard) {
        window.dashboard.closeModal();
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new SRMDashboard();
});
