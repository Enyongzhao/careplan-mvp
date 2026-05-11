"""
Integration tests for API endpoints.
Uses Django test client — real DB, real serializers, real services.
Celery task is mocked so LLM is never called.
"""
import json
import pytest
from unittest.mock import patch
from django.test import Client

from careplan.models import Patient, Provider, Order, CarePlan


MOCK_CELERY = 'careplan.tasks.generate_care_plan.delay'

VALID_PAYLOAD = {
    'patient_first_name': 'John',
    'patient_last_name': 'Doe',
    'mrn': '123456',
    'medication_name': 'Aspirin',
    'primary_diagnosis': 'G70.01',
}


def post_order(client, payload=None, **overrides):
    data = {**(payload or VALID_PAYLOAD), **overrides}
    return client.post(
        '/api/orders/',
        data=json.dumps(data),
        content_type='application/json',
    )


@pytest.fixture
def client():
    return Client()


# ── POST /api/orders/ ────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCreateOrder:

    def test_valid_request_returns_202(self, client):
        with patch(MOCK_CELERY):
            r = post_order(client)
        assert r.status_code == 202
        body = r.json()
        assert 'order_id' in body
        assert 'careplan_id' in body
        assert body['status'] == 'pending'

    def test_creates_pending_careplan_in_db(self, client):
        with patch(MOCK_CELERY):
            r = post_order(client)
        careplan_id = r.json()['careplan_id']
        cp = CarePlan.objects.get(id=careplan_id)
        assert cp.status == 'pending'

    def test_celery_task_is_called_once(self, client):
        with patch(MOCK_CELERY) as mock_delay:
            post_order(client)
        mock_delay.assert_called_once()

    def test_invalid_mrn_returns_400(self, client):
        with patch(MOCK_CELERY):
            r = post_order(client, mrn='abc')
        assert r.status_code == 400
        body = r.json()
        assert body['type'] == 'validation_error'
        assert 'mrn' in body['detail']

    def test_invalid_npi_returns_400(self, client):
        with patch(MOCK_CELERY):
            r = post_order(client, referring_provider_npi='12345', referring_provider='Dr. X')
        assert r.status_code == 400
        body = r.json()
        assert body['type'] == 'validation_error'
        assert 'referring_provider_npi' in body['detail']

    def test_npi_without_provider_name_returns_400(self, client):
        with patch(MOCK_CELERY):
            r = post_order(client, referring_provider_npi='1234567890')
        assert r.status_code == 400
        body = r.json()
        assert body['type'] == 'validation_error'
        assert 'referring_provider' in body['detail']

    def test_npi_conflict_returns_409(self, client):
        Provider.objects.create(name='Dr. Smith', npi='1234567890')
        with patch(MOCK_CELERY):
            r = post_order(client,
                referring_provider_npi='1234567890',
                referring_provider='Dr. Jones',  # different name → conflict
            )
        assert r.status_code == 409
        body = r.json()
        assert body['type'] == 'block_error'
        assert body['code'] == 'provider_npi_conflict'

    def test_same_day_duplicate_order_returns_409(self, client):
        with patch(MOCK_CELERY):
            post_order(client)          # first order
            r = post_order(client)      # same patient + same medication + same day
        assert r.status_code == 409
        body = r.json()
        assert body['code'] == 'duplicate_order_same_day'

    def test_previous_day_duplicate_returns_200_warning(self, client):
        with patch(MOCK_CELERY):
            first = post_order(client)
        # Backdate the first order so it looks like yesterday
        from datetime import timedelta
        from django.utils import timezone
        order_id = first.json()['order_id']
        Order.objects.filter(id=order_id).update(
            created_at=timezone.now() - timedelta(days=1)
        )
        with patch(MOCK_CELERY):
            r = post_order(client)
        assert r.status_code == 200
        body = r.json()
        assert body['type'] == 'warning'
        assert body['code'] == 'duplicate_order'
        assert body['detail']['requires_confirm'] is True

    def test_confirm_true_bypasses_previous_day_warning(self, client):
        with patch(MOCK_CELERY):
            first = post_order(client)
        from datetime import timedelta
        from django.utils import timezone
        order_id = first.json()['order_id']
        Order.objects.filter(id=order_id).update(
            created_at=timezone.now() - timedelta(days=1)
        )
        with patch(MOCK_CELERY):
            r = post_order(client, confirm=True)
        assert r.status_code == 202


# ── GET /api/orders/<id>/ ────────────────────────────────────────────────────

@pytest.mark.django_db
class TestGetOrder:

    def test_existing_order_returns_200(self, client):
        with patch(MOCK_CELERY):
            create_r = post_order(client)
        order_id = create_r.json()['order_id']

        r = client.get(f'/api/orders/{order_id}/')
        assert r.status_code == 200
        body = r.json()
        assert body['mrn'] == '123456'
        assert body['medication_name'] == 'Aspirin'
        assert body['primary_diagnosis'] == 'G70.01'
        assert body['status'] == 'pending'

    def test_nonexistent_order_returns_404(self, client):
        fake_id = '00000000-0000-0000-0000-000000000000'
        r = client.get(f'/api/orders/{fake_id}/')
        assert r.status_code == 404
        body = r.json()
        assert body['type'] == 'not_found'
        assert body['code'] == 'not_found'


# ── GET /api/careplan/<id>/status/ ───────────────────────────────────────────

@pytest.mark.django_db
class TestGetCarePlanStatus:

    def test_pending_careplan_returns_status_only(self, client):
        with patch(MOCK_CELERY):
            create_r = post_order(client)
        careplan_id = create_r.json()['careplan_id']

        r = client.get(f'/api/careplan/{careplan_id}/status/')
        assert r.status_code == 200
        body = r.json()
        assert body['status'] == 'pending'
        assert 'content' not in body   # content absent when pending

    def test_completed_careplan_includes_content(self, client):
        with patch(MOCK_CELERY):
            create_r = post_order(client)
        careplan_id = create_r.json()['careplan_id']
        CarePlan.objects.filter(id=careplan_id).update(status='completed', content='Care plan text.')

        r = client.get(f'/api/careplan/{careplan_id}/status/')
        assert r.status_code == 200
        body = r.json()
        assert body['status'] == 'completed'
        assert body['content'] == 'Care plan text.'

    def test_nonexistent_careplan_returns_404(self, client):
        r = client.get('/api/careplan/99999/status/')
        assert r.status_code == 404
        body = r.json()
        assert body['type'] == 'not_found'
