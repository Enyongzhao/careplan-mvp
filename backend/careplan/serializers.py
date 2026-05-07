from rest_framework import serializers


class OrderDetailSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    status = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()
    patient_first_name = serializers.CharField(source='patient.first_name')
    patient_last_name = serializers.CharField(source='patient.last_name')
    mrn = serializers.CharField(source='patient.mrn')
    medication_name = serializers.CharField()
    primary_diagnosis = serializers.CharField()
    patient_records = serializers.CharField()

    def get_status(self, obj):
        return obj.careplan.status

    def get_content(self, obj):
        return obj.careplan.content


def serialize_careplan_status(care_plan) -> dict:
    data = {'status': care_plan.status}
    if care_plan.status in ('completed', 'failed'):
        data['content'] = care_plan.content
    return data
