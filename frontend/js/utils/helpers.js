/**
 * Utility Helper Functions
 * Contains reusable utility functions used throughout the application
 */

import { TOAST_TYPES, DEFAULT_TOAST_DURATION, TOAST_SHOW_DELAY_MS, TOAST_HIDE_DELAY_MS, API_BASE_URL } from './constants.js';

// Re-export commonly used constants
export { API_BASE_URL };

/**
 * Toast Notification System
 */
export const showToast = (message, type = TOAST_TYPES.INFO, duration = DEFAULT_TOAST_DURATION) => {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <span>${message}</span>
            <button onclick="this.parentElement.parentElement.remove()" 
                    style="background: none; border: none; color: white; font-size: 18px; margin-left: 10px; cursor: pointer;"
                    aria-label="Close notification">&times;</button>
        </div>
    `;
    
    document.body.appendChild(toast);
    
    // Show toast
    setTimeout(() => toast.classList.add('show'), TOAST_SHOW_DELAY_MS);
    
    // Auto remove
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), TOAST_HIDE_DELAY_MS);
    }, duration);
};

/**
 * Loading Spinner Management
 */
// Global loading spinner (reference counted to avoid flicker & duplicates)
let _loadingCount = 0;
let _spinnerEl = null;

const ensureSpinnerElement = () => {
    if (!_spinnerEl) {
        _spinnerEl = document.getElementById('loading-spinner');
    if (!_spinnerEl) {
      _spinnerEl = document.createElement('div');
      _spinnerEl.id = 'loading-spinner';
      _spinnerEl.className = 'loading-spinner';
      _spinnerEl.style.display = 'none';
      // Ensure inner spinner markup exists for consistent styling
      const inner = document.createElement('div');
      inner.className = 'spinner';
      inner.setAttribute('aria-label', 'Loading');
      _spinnerEl.appendChild(inner);
      document.body.appendChild(_spinnerEl);
    }
    }
    return _spinnerEl;
};

export const showLoading = () => {
    const el = ensureSpinnerElement();
    _loadingCount++;
    // Only actually show when transitioning from 0 -> 1
    if (_loadingCount === 1) {
        el.style.display = 'block';
    }
};

export const hideLoading = () => {
    if (_loadingCount > 0) {
        _loadingCount--;
    }
    if (_loadingCount === 0 && _spinnerEl) {
        _spinnerEl.style.display = 'none';
    }
};

export const withGlobalLoading = async (fn, { rethrow = false } = {}) => {
    showLoading();
    try {
        return await fn();
    } catch (e) {
        if (rethrow) throw e; else console.error(e);
        return null;
    } finally {
        hideLoading();
    }
};

/**
 * Authentication State Management
 */
let currentUser = null;
let renderCallback = null;

export const setRenderCallback = (callback) => {
    renderCallback = callback;
};

export const setAuthUser = (user) => {
    currentUser = user;
    if (user) {
        sessionStorage.setItem('srmsUser', JSON.stringify(user));
    } else {
        sessionStorage.removeItem('srmsUser');
        sessionStorage.removeItem('srmsAuth'); // Clear credentials on logout
    }
    // Call render callback if available
    if (renderCallback) {
        renderCallback();
    }
    // Dispatch custom event for components that need to react to auth changes
    window.dispatchEvent(new CustomEvent('authStateChanged', { detail: { user } }));
};

export const getAuthUser = () => currentUser;

export const clearAuthUser = () => setAuthUser(null);

export const isAuthenticated = () => currentUser !== null;

/**
 * Get authentication header for API calls
 */
export const getAuthHeader = () => {
    const storedAuth = sessionStorage.getItem('srmsAuth');
    if (storedAuth) {
        const { username, password } = JSON.parse(storedAuth);
        return 'Basic ' + btoa(`${username}:${password}`);
    }
    return '';
};

// Re-export for convenience in component modules
export { getAuthHeader as authHeader };

/**
 * Debounce function for limiting function calls
 */
export const debounce = (func, wait) => {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
};

/**
 * Format date for display
 */
export const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
};

/**
 * Sanitize HTML to prevent XSS
 */
export const sanitizeHtml = (str) => {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
};

/**
 * Generate unique ID
 */
export const generateId = () => {
    return Math.random().toString(36).substring(2) + Date.now().toString(36);
};

/**
 * Deep clone object
 */
export const deepClone = (obj) => {
    if (obj === null || typeof obj !== 'object') return obj;
    if (obj instanceof Date) return new Date(obj.getTime());
    if (obj instanceof Array) return obj.map(item => deepClone(item));
    
    const cloned = {};
    for (const key in obj) {
        if (obj.hasOwnProperty(key)) {
            cloned[key] = deepClone(obj[key]);
        }
    }
    return cloned;
};

/**
 * Validate email format
 */
export const isValidEmail = (email) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
};

/**
 * Capitalize first letter of string
 */
export const capitalize = (str) => {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
};

/**
 * Format student name for display
 */
export const formatStudentName = (student) => {
    if (!student) return '';
    const firstName = student.first_name || '';
    const lastName = student.last_name || '';
    return `${firstName} ${lastName}`.trim();
};

/**
 * Instructor & Course Material API Helpers
 */
const apiFetch = async (path, options = {}) => {
    const headers = options.headers || {};
    headers['Authorization'] = getAuthHeader();
    if (!(options.body instanceof FormData)) {
        headers['Content-Type'] = headers['Content-Type'] || 'application/json';
    }
    const res = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
    if (!res.ok) {
        let detail = 'Request failed';
        try { const data = await res.json(); detail = data.message || data.detail || JSON.stringify(data); } catch(_) {}
        throw new Error(detail);
    }
    try { return await res.json(); } catch { return {}; }
};

export const fetchInstructorCourses = () => apiFetch('/instructors/me/courses');
export const fetchCourseInstructors = (courseId) => apiFetch(`/courses/${courseId}/instructors`);
export const assignInstructor = (courseId, instructor_username) => apiFetch(`/courses/${courseId}/instructors`, { method: 'POST', body: JSON.stringify({ instructor_username }) });
export const removeInstructor = (courseId, instructorUserId) => apiFetch(`/courses/${courseId}/instructors/${instructorUserId}`, { method: 'DELETE' });
export const listMaterials = (courseId) => apiFetch(`/courses/${courseId}/materials`);
export const addMaterial = (courseId, payload) => apiFetch(`/courses/${courseId}/materials`, { method: 'POST', body: JSON.stringify(payload) });
export const deleteMaterial = (courseId, materialId) => apiFetch(`/courses/${courseId}/materials/${materialId}`, { method: 'DELETE' });
export const instructorGradeEntry = (payload) => apiFetch('/instructor/grades', { method: 'POST', body: JSON.stringify(payload) });

/**
 * UI Initialization for Instructor/Admin Panels
 */
export async function initRoleDashboards(currentUser) {
  try {
    if (currentUser?.role === 'instructor') {
      document.getElementById('instructor-dashboard')?.classList.remove('hidden');
      await renderInstructorCourses();
    }
    if (currentUser?.role === 'admin') {
      document.getElementById('admin-instructor-management')?.classList.remove('hidden');
      await populateCourseSelect();
    }
  } catch (e) {
    console.error('Failed initializing dashboards', e);
  }
}

async function renderInstructorCourses() {
  const container = document.getElementById('instructor-courses');
  if (!container) return;
  container.innerHTML = '<h3 class="font-medium mb-2">My Courses</h3>';
  try {
    const courses = await fetchInstructorCourses();
    if (!courses.length) {
      container.innerHTML += '<p class="text-sm text-neutral-500">No assigned courses yet.</p>';
      return;
    }
    const list = document.createElement('ul');
    list.className = 'space-y-2';
    courses.forEach(c => {
      const li = document.createElement('li');
      li.className = 'border border-neutral-200 rounded p-3 flex flex-col gap-2';
      li.innerHTML = `
        <div class="flex items-center justify-between">
          <span class="font-semibold">${c.course_code || c.code || 'Course'} – ${c.name || c.title || ''}</span>
          <button data-course-id="${c.id}" class="text-xs px-2 py-1 rounded border border-neutral-300 hover:bg-neutral-100 view-materials">Materials</button>
        </div>
        <div class="materials-panel hidden"></div>
      `;
      list.appendChild(li);
    });
    container.appendChild(list);
    container.addEventListener('click', async (evt) => {
      const btn = evt.target.closest('.view-materials');
      if (!btn) return;
      const li = btn.closest('li');
      const panel = li.querySelector('.materials-panel');
      panel.classList.toggle('hidden');
      if (!panel.dataset.loaded) {
        panel.innerHTML = '<p class="text-sm text-neutral-500">Loading materials...</p>';
        const courseId = btn.getAttribute('data-course-id');
        try {
          const mats = await listMaterials(courseId);
          panel.innerHTML = renderMaterialsList(courseId, mats, true);
          panel.dataset.loaded = '1';
          attachMaterialHandlers(panel, courseId, true);
        } catch (e) {
          panel.innerHTML = '<p class="text-sm text-red-600">Failed to load materials.</p>';
        }
      }
    });
  } catch (e) {
    container.innerHTML += '<p class="text-sm text-red-600">Failed to load courses.</p>';
  }
}

async function populateCourseSelect() {
  // Reuse existing endpoint listing all courses if available; fallback to instructor courses fetch
  const select = document.getElementById('assign-course-select');
  if (!select) return;
  select.innerHTML = '<option value="">Loading...</option>';
  try {
    // Attempt generic /courses endpoint if exists
    let courses = [];
    try {
      const resp = await apiFetch('/courses');
      if (Array.isArray(resp)) courses = resp;
    } catch (_) {
      // ignore
    }
    if (!courses.length) {
      courses = await fetchInstructorCourses();
    }
    if (!courses.length) {
      select.innerHTML = '<option value="">No courses</option>';
      return;
    }
    select.innerHTML = '<option value="">Select a course</option>' + courses.map(c => `<option value="${c.id}">${c.course_code || c.code || ''} ${c.name || c.title || ''}</option>`).join('');
    // Load instructors list when course chosen
    select.addEventListener('change', async () => {
      await refreshCourseInstructors();
    });
    document.getElementById('assign-instructor-form')?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const courseId = select.value;
      const userField = document.getElementById('assign-instructor-username');
      const status = document.getElementById('assign-instructor-status');
      if (!courseId) return;
      status.textContent = 'Assigning...';
      try {
        await assignInstructor(courseId, userField.value.trim());
        status.textContent = 'Instructor assigned.';
        userField.value = '';
        await refreshCourseInstructors();
      } catch (err) {
        status.textContent = 'Failed: ' + (err.message || 'Error');
      }
    });
  } catch (e) {
    select.innerHTML = '<option value="">Error loading</option>';
  }
}

async function refreshCourseInstructors() {
  const select = document.getElementById('assign-course-select');
  const list = document.getElementById('course-instructors-list');
  const status = document.getElementById('assign-instructor-status');
  if (!select || !list) return;
  const courseId = select.value;
  list.innerHTML = '';
  if (!courseId) return;
  status.textContent = 'Loading instructors...';
  try {
    const instructors = await fetchCourseInstructors(courseId);
    if (!instructors.length) {
      list.innerHTML = '<li class="text-sm text-neutral-500">None assigned.</li>';
    } else {
      instructors.forEach(i => {
        const li = document.createElement('li');
        li.className = 'flex justify-between items-center border border-neutral-200 rounded px-3 py-2';
        li.innerHTML = `<span>${i.username || i.instructor_username || 'instructor'} (id:${i.instructor_id || i.id})</span>
          <button data-instructor-id="${i.instructor_id || i.id}" class="text-xs px-2 py-1 rounded border border-neutral-300 hover:bg-neutral-100 remove-instructor">Remove</button>`;
        list.appendChild(li);
      });
      list.addEventListener('click', async (evt) => {
        const btn = evt.target.closest('.remove-instructor');
        if (!btn) return;
        const instrId = btn.getAttribute('data-instructor-id');
        try {
          await removeInstructor(courseId, instrId);
          await refreshCourseInstructors();
        } catch (e) {
          status.textContent = 'Remove failed';
        }
      }, { once: true });
    }
    status.textContent = '';
  } catch (e) {
    status.textContent = 'Failed loading instructors';
  }
}

function renderMaterialsList(courseId, materials, editable) {
  if (!materials.length) return '<p class="text-sm text-neutral-500">No materials yet.</p>' + (editable ? materialAddForm(courseId) : '');
  return `
    <div class="flex flex-col gap-2">
      ${editable ? materialAddForm(courseId) : ''}
      <ul class="space-y-1">
        ${materials.map(m => `<li class="flex justify-between items-center border border-neutral-200 rounded px-2 py-1 text-sm">${m.title || m.filename || 'Material'}
          ${editable ? `<button data-material-id="${m.id}" class="text-xs px-2 py-0.5 rounded border border-neutral-300 hover:bg-neutral-100 delete-material">Delete</button>` : ''}
        </li>`).join('')}
      </ul>
    </div>`;
}

function materialAddForm(courseId) {
  return `<form data-course-id="${courseId}" class="add-material-form flex gap-2 items-end">
    <div class="flex-1">
      <input type="text" name="title" placeholder="Material Title" class="border border-neutral-300 rounded px-2 py-1 w-full" required />
    </div>
    <div class="flex-1">
      <input type="url" name="url" placeholder="URL" class="border border-neutral-300 rounded px-2 py-1 w-full" required />
    </div>
    <button type="submit" class="bg-neutral-900 text-white px-3 py-1 rounded text-sm">Add</button>
  </form>`;
}

function attachMaterialHandlers(root, courseId, editable) {
  if (editable) {
    const form = root.querySelector('.add-material-form');
    form?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const fd = new FormData(form);
      try {
        await addMaterial(courseId, { title: fd.get('title'), url: fd.get('url') });
        const updated = await listMaterials(courseId);
        root.innerHTML = renderMaterialsList(courseId, updated, true);
        attachMaterialHandlers(root, courseId, true);
      } catch (e) {
        alert('Add failed');
      }
    });
  }
  root.querySelectorAll('.delete-material').forEach(btn => {
    btn.addEventListener('click', async () => {
      const id = btn.getAttribute('data-material-id');
      try {
        await deleteMaterial(courseId, id);
        const updated = await listMaterials(courseId);
        root.innerHTML = renderMaterialsList(courseId, updated, editable);
        attachMaterialHandlers(root, courseId, editable);
      } catch (e) {
        alert('Delete failed');
      }
    });
  });
  // Wire up grade entry form submission if present
  const gradeForm = root.querySelector('.grade-entry-form');
  if (gradeForm) {
    gradeForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const fd = new FormData(gradeForm);
      try {
        await instructorGradeEntry({ course_id: courseId, grades: Array.from(fd.entries()).map(([studentId, value]) => ({ student_id: studentId, value })) });
        showToast('Grades submitted successfully.', TOAST_TYPES.SUCCESS);
      } catch (e) {
        showToast('Failed to submit grades: ' + (e.message || 'Error'), TOAST_TYPES.ERROR);
      }
    });
  }
}

// Grade Entry Single Form Handler (dashboard level)
(function setupGradeEntry() {
  const form = document.getElementById('grade-entry-form');
  if (!form) return;
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const status = document.getElementById('grade-entry-status');
    status.textContent = 'Submitting...';
    const fd = new FormData(form);
    const payload = {
      student_index: fd.get('student_index'),
      semester_name: fd.get('semester_name'),
      academic_year: fd.get('academic_year'),
      score: parseFloat(fd.get('score'))
    };
    try {
      await instructorGradeEntry(payload);
      status.textContent = 'Submitted.';
      form.reset();
    } catch (err) {
      status.textContent = 'Failed: ' + (err.message || 'Error');
    }
  });
})();