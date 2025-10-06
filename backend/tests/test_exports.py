import re
import pytest

@pytest.mark.order(2)
class TestExports:
    def test_summary_report_excel_headers(self, client, basic_auth_header):
        r = client.get('/admin/reports/summary?format=excel', headers=basic_auth_header)
        assert r.status_code == 200
        # Content-Type for Excel (likely application/vnd.openxmlformats-officedocument.spreadsheetml.sheet)
        ct = r.headers.get('content-type','')
        assert 'spreadsheetml.sheet' in ct
        disp = r.headers.get('content-disposition','')
        assert 'attachment' in disp.lower()
        assert disp.endswith('.xlsx"') or disp.endswith('.xlsx')
        # Basic size sanity check
        assert len(r.content) > 200  # small workbook still > 200 bytes

    def test_summary_report_csv(self, client, basic_auth_header):
        r = client.get('/admin/reports/summary?format=csv', headers=basic_auth_header)
        assert r.status_code == 200
        assert 'text/csv' in r.headers.get('content-type','') or r.headers.get('content-type','').startswith('text/')
        body = r.content.decode(errors='ignore')
        # Expect at least header columns, simplistic check for commas
        assert ',' in body

    def test_personal_report_txt(self, client, basic_auth_header):
        # Need a student index existing; use placeholder 'STUD001' - adjust or seed accordingly
        student_index = 'STUD001'
        r = client.get(f'/admin/reports/personal/{student_index}?format=txt', headers=basic_auth_header)
        assert r.status_code == 200
        assert 'text/plain' in r.headers.get('content-type','')
        assert len(r.content) > 10

    def test_transcript_excel_endpoint(self, client, basic_auth_header):
        student_index = 'STUD001'
        r = client.get(f'/admin/reports/transcript/{student_index}?format=excel', headers=basic_auth_header)
        assert r.status_code == 200
        assert 'spreadsheetml.sheet' in r.headers.get('content-type','')
        assert len(r.content) > 200

    def test_transcript_pdf_endpoint(self, client, basic_auth_header):
        student_index = 'STUD001'
        r = client.get(f'/admin/reports/transcript/{student_index}?format=pdf', headers=basic_auth_header)
        assert r.status_code == 200
        ct = r.headers.get('content-type','').lower()
        # Accept common PDF content type variations
        assert 'application/pdf' in ct
        disp = r.headers.get('content-disposition','')
        assert 'attachment' in disp.lower() or 'filename=' in disp.lower()
        # basic size sanity: a minimal PDF usually > 800 bytes once metadata+one page
        assert len(r.content) > 800
