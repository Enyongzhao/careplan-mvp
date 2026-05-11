"""
Unit tests for service-layer duplicate detection.
All tests hit the real DB (pytest.mark.django_db).
Celery is NOT involved — we test the detection functions directly.
"""
import pytest
from datetime import timedelta
from django.utils import timezone

from careplan.exceptions import BlockError, WarningException
from careplan.models import Patient, Order
from careplan import services


# ── Provider 检测 ─────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestGetOrCreateProvider:

    def test_new_npi_creates_provider(self):
        provider = services.get_or_create_provider(npi='1234567890', name='Dr. Smith')
        assert provider.npi == '1234567890'
        assert provider.name == 'Dr. Smith'

    def test_same_npi_same_name_returns_existing(self, provider):
        result = services.get_or_create_provider(npi='1234567890', name='Dr. Smith')
        assert result.id == provider.id  # same DB row, not a duplicate

    def test_same_npi_different_name_raises_block_error(self, provider):
        with pytest.raises(BlockError) as exc_info:
            services.get_or_create_provider(npi='1234567890', name='Dr. Jones')
        assert exc_info.value.code == 'provider_npi_conflict'
        assert 'Dr. Smith' in exc_info.value.message
        assert 'Dr. Jones' in exc_info.value.message


# ── Patient 检测 ─────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestGetOrCreatePatient:

    def test_new_mrn_creates_patient(self):
        p = services.get_or_create_patient(
            mrn='999999', first_name='Jane', last_name='Roe', date_of_birth=None
        )
        assert p.mrn == '999999'

    def test_same_mrn_same_name_returns_existing(self, patient):
        result = services.get_or_create_patient(
            mrn='123456', first_name='John', last_name='Doe', date_of_birth=None
        )
        assert result.id == patient.id

    def test_same_mrn_different_first_name_raises_warning(self, patient):
        with pytest.raises(WarningException) as exc_info:
            services.get_or_create_patient(
                mrn='123456', first_name='Jane', last_name='Doe', date_of_birth=None
            )
        assert exc_info.value.code == 'patient_mrn_mismatch'

    def test_same_mrn_different_last_name_raises_warning(self, patient):
        with pytest.raises(WarningException) as exc_info:
            services.get_or_create_patient(
                mrn='123456', first_name='John', last_name='Smith', date_of_birth=None
            )
        assert exc_info.value.code == 'patient_mrn_mismatch'

    def test_same_name_and_dob_different_mrn_raises_warning(self):
        from datetime import date
        dob = date(1980, 1, 1)
        Patient.objects.create(
            mrn='111111', first_name='Alice', last_name='Wong', date_of_birth=dob
        )
        with pytest.raises(WarningException) as exc_info:
            services.get_or_create_patient(
                mrn='222222', first_name='Alice', last_name='Wong', date_of_birth=dob
            )
        assert exc_info.value.code == 'patient_duplicate_identity'
        assert exc_info.value.detail['existing_mrn'] == '111111'

    def test_dob_not_provided_skips_dob_check(self, patient):
        """If DOB is omitted, we only check name — name matches so we reuse."""
        result = services.get_or_create_patient(
            mrn='123456', first_name='John', last_name='Doe', date_of_birth=None
        )
        assert result.id == patient.id


# ── Order 检测 ───────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCheckDuplicateOrder:

    def _create_order(self, patient, medication='Aspirin', days_ago=0):
        order = Order.objects.create(
            patient=patient,
            medication_name=medication,
            primary_diagnosis='G70.01',
        )
        if days_ago:
            past = timezone.now() - timedelta(days=days_ago)
            Order.objects.filter(pk=order.pk).update(created_at=past)
        return order

    def test_no_previous_order_passes(self, patient):
        # Should not raise
        services.check_duplicate_order(patient=patient, medication_name='Aspirin', confirm=False)

    def test_same_day_raises_block_error(self, patient):
        self._create_order(patient, days_ago=0)
        with pytest.raises(BlockError) as exc_info:
            services.check_duplicate_order(patient=patient, medication_name='Aspirin', confirm=False)
        assert exc_info.value.code == 'duplicate_order_same_day'

    def test_same_day_block_ignores_confirm(self, patient):
        """Same-day block cannot be bypassed even with confirm=True."""
        self._create_order(patient, days_ago=0)
        with pytest.raises(BlockError):
            services.check_duplicate_order(patient=patient, medication_name='Aspirin', confirm=True)

    def test_different_day_without_confirm_raises_warning(self, patient):
        self._create_order(patient, days_ago=3)
        with pytest.raises(WarningException) as exc_info:
            services.check_duplicate_order(patient=patient, medication_name='Aspirin', confirm=False)
        assert exc_info.value.code == 'duplicate_order'
        assert exc_info.value.detail['requires_confirm'] is True

    def test_different_day_with_confirm_passes(self, patient):
        """confirm=True skips the previous-day warning."""
        self._create_order(patient, days_ago=3)
        # Should NOT raise
        services.check_duplicate_order(patient=patient, medication_name='Aspirin', confirm=True)

    def test_different_medication_same_day_passes(self, patient):
        self._create_order(patient, medication='Aspirin', days_ago=0)
        # Different medication — should not raise
        services.check_duplicate_order(patient=patient, medication_name='Ibuprofen', confirm=False)
