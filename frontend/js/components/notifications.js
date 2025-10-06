// notifications.js - Client for SSE notifications stream and simple UI hooks
import { API_BASE_URL, showToast, getAuthHeader } from '../utils/helpers.js';

let evtSource = null;

export function connectNotificationsStream() {
    if (evtSource) {
        return; // already connected
    }
    const headers = { 'Authorization': getAuthHeader() };
    // Use fetch to obtain a session cookie? Basic auth works with EventSource only via embedding credentials in URL not recommended.
    // We'll fallback to polling if browser blocks due to auth.
    try {
        const url = `${API_BASE_URL}/notifications/stream`;
        evtSource = new EventSource(url, { withCredentials: false });
        evtSource.onmessage = (ev) => {
            try {
                const parsed = JSON.parse(ev.data);
                handleEvent(parsed.event, parsed.data);
            } catch (e) {
                console.debug('Non JSON SSE message', ev.data);
            }
        };
        evtSource.onerror = () => {
            console.warn('Notifications SSE error; closing and will not retry automatically');
            evtSource.close();
            evtSource = null;
        };
    } catch (e) {
        console.error('Failed to connect SSE stream', e);
    }
}

function handleEvent(event, data) {
    switch (event) {
        case 'hello':
            console.info('SSE hello', data);
            break;
        case 'notification.new':
            showToast(`New notification: ${data.title}`, 'info');
            break;
        case 'notification.read':
            console.info('Notification read event', data);
            break;
        case 'notification.read_all':
            showToast(`All notifications marked read (${data.count})`, 'success');
            break;
        default:
            break;
    }
}

export async function fetchNotifications(unreadOnly = false, limit = 20) {
    const resp = await fetch(`${API_BASE_URL}/notifications?unread_only=${unreadOnly}&limit=${limit}`, {
        headers: { 'Authorization': getAuthHeader() }
    });
    if (!resp.ok) throw new Error('Failed to fetch notifications');
    return resp.json();
}
