from django.utils import timezone

from .exceptions import BlockError, WarningException
from .models import Patient, Provider, Order, CarePlan
from .tasks import generate_care_plan


# ── Provider 检测 ─────────────────────────────────────────────────────────────

def get_or_create_provider(npi: str, name: str) -> Provider:
    try:
        existing = Provider.objects.get(npi=npi)
    except Provider.DoesNotExist:
        return Provider.objects.create(npi=npi, name=name)

    if existing.name != name:
        raise BlockError(
            message=f"NPI {npi} already registered to '{existing.name}', cannot reassign to '{name}'.",
            code='provider_npi_conflict',
            detail={'existing_name': existing.name, 'requested_name': name},
        )
    return existing


# ── Patient 检测 ─────────────────────────────────────────────────────────────

def get_or_create_patient(mrn: str, first_name: str, last_name: str, date_of_birth) -> Patient:
    try:
        existing = Patient.objects.get(mrn=mrn)
    except Patient.DoesNotExist:
        existing = None

    if existing:
        name_matches = (existing.first_name == first_name and existing.last_name == last_name)
        # 如果请求没带 DOB 就不检查 DOB，带了才比对
        dob_matches = (date_of_birth is None or existing.date_of_birth == date_of_birth)

        if name_matches and dob_matches:
            return existing  # 完全匹配，复用

        raise WarningException(
            message=f"MRN {mrn} belongs to '{existing.first_name} {existing.last_name}' "
                    f"(DOB {existing.date_of_birth}), but request has '{first_name} {last_name}' "
                    f"(DOB {date_of_birth}). Please verify patient identity.",
            code='patient_mrn_mismatch',
            detail={
                'existing': {'name': f'{existing.first_name} {existing.last_name}', 'dob': str(existing.date_of_birth)},
                'requested': {'name': f'{first_name} {last_name}', 'dob': str(date_of_birth)},
            },
        )

    # MRN 没找到，再按姓名+DOB 查，防止同一个人用不同 MRN 重复注册
    if date_of_birth:
        duplicate = Patient.objects.filter(
            first_name=first_name,
            last_name=last_name,
            date_of_birth=date_of_birth,
        ).first()
        if duplicate:
            raise WarningException(
                message=f"Patient '{first_name} {last_name}' (DOB {date_of_birth}) already exists "
                        f"with MRN {duplicate.mrn}. Did you mean to use that MRN?",
                code='patient_duplicate_identity',
                detail={'existing_mrn': duplicate.mrn},
            )

    return Patient.objects.create(
        mrn=mrn,
        first_name=first_name,
        last_name=last_name,
        date_of_birth=date_of_birth,
    )


# ── Order 检测 ───────────────────────────────────────────────────────────────

def check_duplicate_order(patient: Patient, medication_name: str, confirm: bool) -> None:
    today = timezone.now().date()

    # 同一天 → 必须阻止，confirm 也救不了
    same_day_exists = Order.objects.filter(
        patient=patient,
        medication_name=medication_name,
        created_at__date=today,
    ).exists()
    if same_day_exists:
        raise BlockError(
            message=f"An order for '{medication_name}' was already submitted today. Same-day duplicates are not allowed.",
            code='duplicate_order_same_day',
        )

    # 不同天 → 警告，confirm=True 可绕过
    if not confirm:
        previous_exists = Order.objects.filter(
            patient=patient,
            medication_name=medication_name,
        ).exists()
        if previous_exists:
            raise WarningException(
                message=f"A previous order for '{medication_name}' already exists for this patient.",
                code='duplicate_order',
                detail={'requires_confirm': True},
            )


# ── 主业务函数 ────────────────────────────────────────────────────────────────

def create_order_with_careplan(data: dict) -> tuple:
    confirm = str(data.get('confirm', '')).lower() == 'true'

    print(f"[DEBUG services] received data keys={list(data.keys())}, confirm={confirm}")

    # Provider（可选，只有前端传了 npi 才检测）
    provider = None
    if data.get('npi'):
        provider = get_or_create_provider(
            npi=data['npi'],
            name=data.get('provider_name', ''),
        )

    patient = get_or_create_patient(
        mrn=data.get('mrn', ''),
        first_name=data.get('patient_first_name', ''),
        last_name=data.get('patient_last_name', ''),
        date_of_birth=data.get('date_of_birth'),
    )
    print(f"[DEBUG services] patient={patient.first_name} {patient.last_name}, db_id={patient.id}")

    check_duplicate_order(
        patient=patient,
        medication_name=data.get('medication_name', ''),
        confirm=confirm,
    )

    order = Order.objects.create(
        patient=patient,
        provider=provider,
        medication_name=data.get('medication_name', ''),
        primary_diagnosis=data.get('primary_diagnosis', ''),
        additional_diagnoses=data.get('additional_diagnoses', ''),
        medication_history=data.get('medication_history', ''),
        patient_records=data.get('patient_records', ''),
    )
    print(f"[DEBUG services] order created, id={order.id}")

    care_plan = CarePlan.objects.create(order=order, status='pending')
    print(f"[DEBUG services] care_plan created, id={care_plan.id}, status={care_plan.status}")

    generate_care_plan.delay(care_plan.id)
    print(f"[DEBUG services] task dispatched to Celery, careplan_id={care_plan.id}")

    return order, care_plan


def get_careplan(careplan_id: int) -> CarePlan:
    return CarePlan.objects.get(id=careplan_id)


def get_order_detail(order_id: str) -> Order:
    return Order.objects.select_related('patient', 'careplan').get(id=order_id)
