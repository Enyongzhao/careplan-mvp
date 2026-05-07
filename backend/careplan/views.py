from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Patient, Order, CarePlan
from .tasks import generate_care_plan


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

    generate_care_plan.delay(care_plan.id)

    return Response({'order_id': str(order.id), 'careplan_id': care_plan.id, 'status': 'pending'}, status=202)


@api_view(['GET'])
def get_careplan_status(request, careplan_id):
    try:
        care_plan = CarePlan.objects.get(id=careplan_id)
    except CarePlan.DoesNotExist:
        return Response({'error': 'CarePlan not found'}, status=404)

    data = {'status': care_plan.status}
    if care_plan.status in ('completed', 'failed'):
        data['content'] = care_plan.content
    return Response(data)


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
