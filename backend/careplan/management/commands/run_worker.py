import redis
from django.conf import settings
from django.core.management.base import BaseCommand

from careplan.models import CarePlan
from careplan.views import call_llm


class Command(BaseCommand):
    help = "Worker: pull careplan jobs from Redis and call LLM"

    def handle(self, *args, **options):
        r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)
        queue = settings.REDIS_CAREPLAN_QUEUE

        self.stdout.write(f"Worker started. Listening on queue '{queue}' ...")

        while True:
            # blpop blocks until an item arrives; returns (queue_name, value)
            _, careplan_id = r.blpop(queue)
            self.stdout.write(f"Picked up careplan_id={careplan_id}")

            try:
                care_plan = CarePlan.objects.select_related('order__patient').get(id=careplan_id)
            except CarePlan.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"  CarePlan {careplan_id} not found, skipping."))
                continue

            care_plan.status = 'processing'
            care_plan.save(update_fields=['status'])

            try:
                care_plan.content = call_llm(care_plan.order, care_plan.order.patient)
                care_plan.status = 'completed'
                self.stdout.write(self.style.SUCCESS(f"  Done: careplan_id={careplan_id}"))
            except Exception as e:
                care_plan.status = 'failed'
                care_plan.content = str(e)
                self.stdout.write(self.style.ERROR(f"  Failed: {e}"))

            care_plan.save(update_fields=['status', 'content'])
