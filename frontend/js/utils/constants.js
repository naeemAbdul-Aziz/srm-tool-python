/**
 * Application Constants
 * Contains configuration values and constants used throughout the application
 */

// API Configuration
export const API_BASE_URL = 'http://127.0.0.1:8000';

// Toast Types
export const TOAST_TYPES = {
    SUCCESS: 'success',
    ERROR: 'error',
    INFO: 'info',
    WARNING: 'warning'
};

// Default Values
export const DEFAULT_PAGE_SIZE = 20;
export const DEFAULT_DEBOUNCE_MS = 300;
export const DEFAULT_TOAST_DURATION = 4000;

// Pagination Settings
export const PAGE_SIZE_OPTIONS = [10, 20, 50, 100];

// Cache Settings
export const CACHE_SIZE = 1000;
export const PREFETCH_PAGES = 2;

// UI Constants
export const LOADING_DELAY_MS = 100;
export const TOAST_SHOW_DELAY_MS = 100;
export const TOAST_HIDE_DELAY_MS = 300;