"""
Unit tests for CreateOrderSerializer.
No database needed — serializers only validate Python dicts.
"""
import pytest
from careplan.serializers import CreateOrderSerializer

VALID = {
    'patient_first_name': 'John',
    'patient_last_name': 'Doe',
    'mrn': '123456',
    'medication_name': 'Aspirin',
    'primary_diagnosis': 'G70.01',
}


def _invalid(overrides):
    """Return VALID dict with specific fields overridden."""
    return {**VALID, **overrides}


# ── 合法输入 ──────────────────────────────────────────────────────────────────

def test_valid_minimal_input_passes():
    s = CreateOrderSerializer(data=VALID)
    assert s.is_valid(), s.errors


def test_valid_with_npi_and_provider_passes():
    s = CreateOrderSerializer(data=_invalid({
        'referring_provider_npi': '1234567890',
        'referring_provider': 'Dr. Smith',
    }))
    assert s.is_valid(), s.errors


def test_source_mapping_npi_to_npi_key():
    """referring_provider_npi in input → 'npi' in validated_data."""
    s = CreateOrderSerializer(data=_invalid({
        'referring_provider_npi': '1234567890',
        'referring_provider': 'Dr. Smith',
    }))
    s.is_valid()
    assert s.validated_data['npi'] == '1234567890'
    assert s.validated_data['provider_name'] == 'Dr. Smith'


def test_confirm_defaults_to_false():
    s = CreateOrderSerializer(data=VALID)
    s.is_valid()
    assert s.validated_data['confirm'] is False


# ── MRN 格式 ─────────────────────────────────────────────────────────────────

def test_mrn_letters_fails():
    s = CreateOrderSerializer(data=_invalid({'mrn': 'abcdef'}))
    assert not s.is_valid()
    assert 'mrn' in s.errors


def test_mrn_too_short_fails():
    s = CreateOrderSerializer(data=_invalid({'mrn': '12345'}))
    assert not s.is_valid()
    assert 'mrn' in s.errors


def test_mrn_too_long_fails():
    s = CreateOrderSerializer(data=_invalid({'mrn': '1234567'}))
    assert not s.is_valid()
    assert 'mrn' in s.errors


def test_mrn_exactly_6_digits_passes():
    s = CreateOrderSerializer(data=_invalid({'mrn': '000000'}))
    assert s.is_valid(), s.errors


# ── NPI 格式 ─────────────────────────────────────────────────────────────────

def test_npi_too_short_fails():
    s = CreateOrderSerializer(data=_invalid({
        'referring_provider_npi': '123456789',   # 9 digits
        'referring_provider': 'Dr. Smith',
    }))
    assert not s.is_valid()
    assert 'referring_provider_npi' in s.errors


def test_npi_with_letters_fails():
    s = CreateOrderSerializer(data=_invalid({
        'referring_provider_npi': '123456789X',
        'referring_provider': 'Dr. Smith',
    }))
    assert not s.is_valid()
    assert 'referring_provider_npi' in s.errors


def test_npi_blank_is_allowed():
    """NPI is optional — blank string should pass."""
    s = CreateOrderSerializer(data=_invalid({'referring_provider_npi': ''}))
    assert s.is_valid(), s.errors


# ── NPI + Provider 跨字段规则 ─────────────────────────────────────────────────

def test_npi_without_provider_name_fails():
    s = CreateOrderSerializer(data=_invalid({
        'referring_provider_npi': '1234567890',
        # referring_provider intentionally omitted
    }))
    assert not s.is_valid()
    assert 'referring_provider' in s.errors


def test_provider_name_without_npi_passes():
    """Provider name alone (no NPI) is fine."""
    s = CreateOrderSerializer(data=_invalid({'referring_provider': 'Dr. Smith'}))
    assert s.is_valid(), s.errors


# ── ICD-10 格式 ───────────────────────────────────────────────────────────────

def test_icd10_no_dot_passes():
    s = CreateOrderSerializer(data=_invalid({'primary_diagnosis': 'I10'}))
    assert s.is_valid(), s.errors


def test_icd10_with_dot_passes():
    s = CreateOrderSerializer(data=_invalid({'primary_diagnosis': 'G70.01'}))
    assert s.is_valid(), s.errors


def test_icd10_starts_with_digit_fails():
    s = CreateOrderSerializer(data=_invalid({'primary_diagnosis': '70.01'}))
    assert not s.is_valid()
    assert 'primary_diagnosis' in s.errors


def test_icd10_only_letters_fails():
    s = CreateOrderSerializer(data=_invalid({'primary_diagnosis': 'GOUT'}))
    assert not s.is_valid()
    assert 'primary_diagnosis' in s.errors


# ── 姓名格式 ─────────────────────────────────────────────────────────────────

def test_first_name_with_digits_fails():
    s = CreateOrderSerializer(data=_invalid({'patient_first_name': 'John2'}))
    assert not s.is_valid()
    assert 'patient_first_name' in s.errors


def test_last_name_with_special_chars_fails():
    s = CreateOrderSerializer(data=_invalid({'patient_last_name': 'Doe!'}))
    assert not s.is_valid()
    assert 'patient_last_name' in s.errors
