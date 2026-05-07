from .models import Patient, Order, CarePlan
from .tasks import generate_care_plan


def create_order_with_careplan(data: dict) -> tuple:
    # DEBUG ② services.py — 收到 views 传来的 dict，开始操作数据库
    print(f"[DEBUG services] received data type={type(data)}, keys={list(data.keys())}")

    patient, created = Patient.objects.get_or_create(
        mrn=data.get('mrn', ''),
        defaults={
            'first_name': data.get('patient_first_name', ''),
            'last_name': data.get('patient_last_name', ''),
        }
    )
    # patient 是 Django ORM 实例，created 说明是新建还是已存在
    print(f"[DEBUG services] patient={patient.first_name} {patient.last_name}, db_id={patient.id}, created={created}")

    order = Order.objects.create(
        patient=patient,
        medication_name=data.get('medication_name', ''),
        primary_diagnosis=data.get('primary_diagnosis', ''),
        additional_diagnoses=data.get('additional_diagnoses', ''),
        medication_history=data.get('medication_history', ''),
        patient_records=data.get('patient_records', ''),
    )
    # order.id 是 UUID，刚写进数据库
    print(f"[DEBUG services] order created, id={order.id} (type={type(order.id).__name__})")

    care_plan = CarePlan.objects.create(order=order, status='pending')
    print(f"[DEBUG services] care_plan created, id={care_plan.id}, status={care_plan.status}")

    # DEBUG ③ services.py — 把任务 id 推进 Redis，立刻返回，不等 LLM
    generate_care_plan.delay(care_plan.id)
    print(f"[DEBUG services] task dispatched to Celery, careplan_id={care_plan.id}")

    return order, care_plan


def get_careplan(careplan_id: int) -> CarePlan:
    return CarePlan.objects.get(id=careplan_id)


def get_order_detail(order_id: str) -> Order:
    return Order.objects.select_related('patient', 'careplan').get(id=order_id)
