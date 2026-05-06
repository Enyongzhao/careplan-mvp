import redis
import openai
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Patient, Order, CarePlan


def _get_redis():
    return redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)


@api_view(['POST'])
def create_order(request):
    data = request.data

    patient, _ = Patient.objects.get_or_create(
        mrn=data.get('mrn', ''),
        defaults={
            'first_name': data.get('patient_first_name', ''),
            'last_name': data.get('patient_last_name', ''),
        }
    )

    order = Order.objects.create(
        patient=patient,
        medication_name=data.get('medication_name', ''),
        primary_diagnosis=data.get('primary_diagnosis', ''),
        additional_diagnoses=data.get('additional_diagnoses', ''),
        medication_history=data.get('medication_history', ''),
        patient_records=data.get('patient_records', ''),
    )

    care_plan = CarePlan.objects.create(order=order, status='pending')

    _get_redis().rpush(settings.REDIS_CAREPLAN_QUEUE, str(care_plan.id))

    return Response({'order_id': str(order.id), 'careplan_id': care_plan.id, 'status': 'pending'}, status=202)


@api_view(['GET'])
def get_order(request, order_id):
    try:
        order = Order.objects.select_related('patient', 'careplan').get(id=order_id)
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=404)

    return Response(_build_response(order, order.patient, order.careplan))


def _build_response(order, patient, care_plan):
    return {
        'id': str(order.id),
        'status': care_plan.status,
        'content': care_plan.content,
        'patient_first_name': patient.first_name,
        'patient_last_name': patient.last_name,
        'mrn': patient.mrn,
        'medication_name': order.medication_name,
        'primary_diagnosis': order.primary_diagnosis,
        'patient_records': order.patient_records,
    }


def call_llm(order, patient):
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
