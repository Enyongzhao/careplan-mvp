import openai
from celery import shared_task
from django.conf import settings

from .models import CarePlan


@shared_task(bind=True, max_retries=3)
def generate_care_plan(self, careplan_id):
    try:
        care_plan = CarePlan.objects.select_related('order__patient').get(id=careplan_id)
    except CarePlan.DoesNotExist:
        # Record is gone — nothing to retry
        return

    care_plan.status = 'processing'
    care_plan.save(update_fields=['status'])

    try:
        order = care_plan.order
        patient = order.patient
        care_plan.content = _call_llm(order, patient)
        care_plan.status = 'completed'
        care_plan.save(update_fields=['status', 'content'])
    except Exception as exc:
        care_plan.status = 'pending'
        care_plan.save(update_fields=['status'])
        # 指数退避: 第1次重试等30s，第2次60s，第3次120s
        raise self.retry(exc=exc, countdown=30 * (2 ** self.request.retries))


def _call_llm(order, patient):
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

    prompt = f"""You are a clinical pharmacist. Generate a professional care plan for this patient.

Patient Information:
- Name: {patient.first_name} {patient.last_name}
- MRN: {patient.mrn}
- Primary Diagnosis: {order.primary_diagnosis}
- Medication: {order.medication_name}
- Patient Records: {order.patient_records}

Generate a care plan with these sections:
1. Problem List / Drug Therapy Problems (DTPs)
2. Goals (SMART)
3. Pharmacist Interventions / Plan
4. Monitoring Plan & Lab Schedule

Be specific and clinical."""

    response = client.chat.completions.create(
        model='gpt-4o',
        messages=[{'role': 'user', 'content': prompt}],
        max_tokens=1024,
    )
    return response.choices[0].message.content
