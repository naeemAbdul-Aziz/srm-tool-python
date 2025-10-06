import time
import pytest

@pytest.mark.order(1)
@pytest.mark.usefixtures('client')
class TestNotifications:
    def test_list_notifications_initial(self, client, basic_auth_header):
        r = client.get('/notifications', headers=basic_auth_header)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_create_admin_notification(self, client, basic_auth_header):
        payload = {
            'type': 'system',
            'title': 'Test Notice',
            'message': 'Test message body',
            'severity': 'info',
            'audience': 'admins'
        }
        r = client.post('/admin/notifications', json=payload, headers=basic_auth_header)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get('success') is True
        assert 'notification_id' in data.get('data', {})

    def test_unread_count_and_mark_read_flow(self, client, basic_auth_header):
        # Create a new notification to ensure unread exists
        payload = {
            'type': 'system',
            'title': 'Unread Flow',
            'message': 'Ensure unread increment',
            'severity': 'info',
            'audience': 'admins'
        }
        client.post('/admin/notifications', json=payload, headers=basic_auth_header)
        r = client.get('/notifications/unread-count', headers=basic_auth_header)
        assert r.status_code == 200
        unread_before = r.json().get('unread', 0)
        assert unread_before >= 1

        # Fetch list and mark first unread as read
        list_resp = client.get('/notifications', headers=basic_auth_header)
        first = next((n for n in list_resp.json() if not n.get('read_at')), None)
        assert first is not None, 'Expected at least one unread notification'
        nid = first.get('user_notification_id') or first.get('id')
        mark_resp = client.post(f'/notifications/{nid}/read', headers=basic_auth_header)
        assert mark_resp.status_code == 200

        # Recount
        r2 = client.get('/notifications/unread-count', headers=basic_auth_header)
        assert r2.status_code == 200
        unread_after = r2.json().get('unread', 0)
        assert unread_after <= unread_before - 1

    def test_mark_all_read(self, client, basic_auth_header):
        r = client.post('/notifications/read-all', headers=basic_auth_header)
        assert r.status_code == 200
        count = r.json().get('updated')
        assert isinstance(count, int)
        # After marking all, unread should be 0
        r2 = client.get('/notifications/unread-count', headers=basic_auth_header)
        assert r2.status_code == 200
        assert r2.json().get('unread') == 0
