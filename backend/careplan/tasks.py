from celery import shared_task

from .models import CarePlan
from .llm_services import get_llm_service


@shared_task(bind=True, max_retries=3)
def generate_care_plan(self, careplan_id):
    try:
        care_plan = CarePlan.objects.select_related('order__patient').get(id=careplan_id)
    except CarePlan.DoesNotExist:
        return

    care_plan.status = 'processing'
    care_plan.save(update_fields=['status'])

    try:
        order = care_plan.order
        patient = order.patient
        care_plan.content = get_llm_service().generate_care_plan(order, patient)
        care_plan.status = 'completed'
        care_plan.save(update_fields=['status', 'content'])
    except Exception as exc:
        care_plan.status = 'pending'
        care_plan.save(update_fields=['status'])
        raise self.retry(exc=exc, countdown=30 * (2 ** self.request.retries))
