import os
import pytest
from comprehensive_seed import seed_comprehensive_database
from db import connect_to_db

@pytest.mark.exhaustive
@pytest.mark.order(10)
def test_exhaustive_seed_creates_assessments_and_notifications(monkeypatch):
    # Run exhaustive seed with suppression off
    assert seed_comprehensive_database(
        num_students=40,
        cleanup_first=True,
        random_seed=321,
        suppress_notifications=False,
        exhaustive=True,
        assessments_sample=15,
        full_reset=True
    )
    conn = connect_to_db(); assert conn
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM assessments")
        result = cur.fetchone()
        assessments = result[0] if result else 0
        cur.execute("SELECT COUNT(*) FROM notifications")
        result = cur.fetchone()
        notifications = result[0] if result else 0
        cur.execute("SELECT COUNT(*) FROM user_notifications")
        result = cur.fetchone()
        user_notifs = result[0] if result else 0
    conn.close()
    assert assessments >= 45  # 3 * 15 sample
    assert notifications >= 3
    assert user_notifs >= notifications  # at least one link per notification

@pytest.mark.exhaustive
@pytest.mark.order(11)
def test_exhaustive_seed_with_suppression(monkeypatch):
    # Run again with notification suppression
    assert seed_comprehensive_database(
        num_students=20,
        cleanup_first=True,
        random_seed=321,
        suppress_notifications=True,
        exhaustive=True,
        assessments_sample=10,
    )
    conn = connect_to_db(); assert conn
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM notifications")
        result = cur.fetchone()
        notifications = result[0] if result else 0
    conn.close()
    # Expect zero notifications due to suppression
    assert notifications == 0
