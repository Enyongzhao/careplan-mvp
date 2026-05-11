import pytest
from careplan.models import Patient, Provider


@pytest.fixture
def patient(db):
    return Patient.objects.create(
        first_name='John',
        last_name='Doe',
        mrn='123456',
    )


@pytest.fixture
def provider(db):
    return Provider.objects.create(
        name='Dr. Smith',
        npi='1234567890',
    )


# 所有 POST 测试共用的合法请求体
VALID_ORDER_PAYLOAD = {
    'patient_first_name': 'John',
    'patient_last_name': 'Doe',
    'mrn': '123456',
    'medication_name': 'Aspirin',
    'primary_diagnosis': 'G70.01',
}
