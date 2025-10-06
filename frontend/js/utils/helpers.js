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