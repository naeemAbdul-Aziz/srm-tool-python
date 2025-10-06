// assessments.js - Minimal client helpers for assessments CRUD
import { API_BASE_URL, getAuthHeader, showToast } from '../utils/helpers.js';

export async function listAssessments(courseCode = null) {
    const url = new URL(`${API_BASE_URL}/assessments`);
    if (courseCode) url.searchParams.set('course_code', courseCode);
    const resp = await fetch(url.toString(), { headers: { 'Authorization': getAuthHeader() } });
    if (!resp.ok) throw new Error('Failed to list assessments');
    return resp.json();
}

export async function createAssessment(payload) {
    const resp = await fetch(`${API_BASE_URL}/assessments`, {
        method: 'POST',
        headers: {
            'Authorization': getAuthHeader(),
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    });
    const data = await resp.json();
    if (!resp.ok || !data.success) throw new Error(data.detail || data.error || 'Create failed');
    showToast('Assessment created', 'success');
    return data.data;
}

export async function updateAssessment(id, payload) {
    const resp = await fetch(`${API_BASE_URL}/assessments/${id}`, {
        method: 'PUT',
        headers: {
            'Authorization': getAuthHeader(),
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    });
    const data = await resp.json();
    if (!resp.ok || !data.success) throw new Error(data.detail || data.error || 'Update failed');
    showToast('Assessment updated', 'success');
    return true;
}

export async function deleteAssessment(id) {
    const resp = await fetch(`${API_BASE_URL}/assessments/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': getAuthHeader() }
    });
    const data = await resp.json();
    if (!resp.ok || !data.success) throw new Error(data.detail || data.error || 'Delete failed');
    showToast('Assessment deleted', 'info');
    return true;
}
