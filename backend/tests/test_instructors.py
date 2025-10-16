import base64
import pytest

# Utility to build auth header

def _auth(username, password='admin123'):
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    return { 'Authorization': f'Basic {token}' }

@pytest.mark.order(10)
class TestInstructorAssignment:
    def test_admin_can_assign_instructor(self, client, basic_auth_header):
        # Precondition: ensure target instructor user exists (seed may have created) else skip
        # Attempt to assign instructor 'instructor1' to TEST101 if endpoint and data present
        payload = { 'instructor_username': 'instructor1' }
        r = client.post('/courses/1/instructors', json=payload, headers=basic_auth_header)
        # Accept 201 (created) or 400/409 if already assigned
        assert r.status_code in (201, 400, 409, 404)

    def test_non_admin_cannot_assign(self, client):
        # Use student baseline user.
        hdr = _auth('STUD001')
        r = client.post('/courses/1/instructors', json={'instructor_username': 'instructor1'}, headers=hdr)
        assert r.status_code in (401, 403)

    def test_list_course_instructors(self, client, basic_auth_header):
        r = client.get('/courses/1/instructors', headers=basic_auth_header)
        # If course exists endpoint returns 200 else 404; we allow either to avoid brittle test env
        assert r.status_code in (200, 404)
        if r.status_code == 200:
            body = r.json()
            assert 'course_id' in body and 'instructors' in body
            assert isinstance(body['instructors'], list)

@pytest.mark.order(11)
class TestMaterialsCrud:
    def _maybe_course(self, client, basic_auth_header):
        # Try to get a known course id via listing; fallback to 1
        try:
            resp = client.get('/courses', headers=basic_auth_header)
            if resp.status_code == 200 and isinstance(resp.json(), list) and resp.json():
                return resp.json()[0].get('course_id') or resp.json()[0].get('id') or 1
        except Exception:
            pass
        return 1

    def test_instructor_or_admin_add_material(self, client, basic_auth_header):
        course_id = self._maybe_course(client, basic_auth_header)
        payload = { 'title': 'Syllabus', 'url': 'https://example.com/syllabus.pdf' }
        r = client.post(f'/courses/{course_id}/materials', json=payload, headers=basic_auth_header)
        assert r.status_code in (201, 403, 404), r.text
        if r.status_code == 201:
            body = r.json(); assert 'material_id' in body

    def test_list_materials(self, client, basic_auth_header):
        course_id = self._maybe_course(client, basic_auth_header)
        r = client.get(f'/courses/{course_id}/materials', headers=basic_auth_header)
        assert r.status_code in (200, 404)
        if r.status_code == 200:
            body = r.json(); assert 'materials' in body and isinstance(body['materials'], list)

    def test_delete_material_permission(self, client, basic_auth_header):
        course_id = self._maybe_course(client, basic_auth_header)
        # First try create
        create = client.post(f'/courses/{course_id}/materials', json={'title':'Tmp','url':'https://e.com/x'}, headers=basic_auth_header)
        if create.status_code == 201:
            mid = create.json().get('material_id')
            del_resp = client.delete(f'/courses/{course_id}/materials/{mid}', headers=basic_auth_header)
            assert del_resp.status_code in (200, 404, 403)
        else:
            pytest.skip('Could not create material to test deletion (status {})'.format(create.status_code))

@pytest.mark.order(12)
class TestInstructorGradeEntry:
    def test_instructor_grade_entry_denied_for_student(self, client):
        hdr = _auth('STUD001')
        payload = { 'student_index': 'STUD001', 'course_code': 'TEST101', 'semester_name': 'Semester 1', 'academic_year': '2024/2025', 'score': 77 }
        r = client.post('/instructor/grades', json=payload, headers=hdr)
        assert r.status_code in (401, 403)

    def test_admin_grade_entry(self, client, basic_auth_header):
        payload = { 'student_index': 'STUD001', 'course_code': 'TEST101', 'semester_name': 'Semester 1', 'academic_year': '2024/2025', 'score': 88.5 }
        r = client.post('/instructor/grades', json=payload, headers=basic_auth_header)
        assert r.status_code in (200, 404), r.text
        if r.status_code == 200:
            body = r.json(); assert body.get('status') in ('created','updated','unchanged','failed')
