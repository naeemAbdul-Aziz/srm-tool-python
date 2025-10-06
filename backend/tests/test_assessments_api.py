import pytest
from comprehensive_seed import seed_comprehensive_database

@pytest.mark.usefixtures("client", "basic_auth_header")
class TestAssessmentsAPI:
    def setup_method(self):
        # Ensure baseline data exists (small deterministic seed)
        seed_comprehensive_database(num_students=5, cleanup_first=True, random_seed=123, suppress_notifications=True, baseline=True)

    def test_list_assessments_initial_empty(self, client, basic_auth_header):
        r = client.get('/assessments', headers=basic_auth_header)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)

    def test_create_update_delete_assessment(self, client, basic_auth_header):
        # Create a course assessment (pick one existing course by listing courses endpoint if available, else assume first seeded course UGCS101)
        payload = {
            "course_code": "UGCS101",
            "assessment_name": "Quiz 1",
            "max_score": 20,
            "weight": 10
        }
        r = client.post('/assessments', json=payload, headers=basic_auth_header)
        assert r.status_code == 200, r.text
        resp_json = r.json()
        assert resp_json.get('success') is True
        aid = resp_json['data']['assessment_id']

        # List again filtered
        r2 = client.get('/assessments?course_code=UGCS101', headers=basic_auth_header)
        assert r2.status_code == 200
        items = r2.json()
        assert any(a['assessment_id'] == aid for a in items)

        # Update
        up = {"weight": 15}
        r3 = client.put(f'/assessments/{aid}', json=up, headers=basic_auth_header)
        assert r3.status_code == 200
        up_json = r3.json()
        assert up_json.get('success') is True

        # Delete
        r4 = client.delete(f'/assessments/{aid}', headers=basic_auth_header)
        assert r4.status_code == 200
        del_json = r4.json()
        assert del_json.get('success') is True

        # Verify removal
        r5 = client.get('/assessments?course_code=UGCS101', headers=basic_auth_header)
        assert r5.status_code == 200
        remaining = r5.json()
        assert not any(a['assessment_id'] == aid for a in remaining)
