import re
from rest_framework import serializers


class CreateOrderSerializer(serializers.Serializer):
    # ── 必填字段 ────────────────────────────────────────────────────────────
    patient_first_name = serializers.CharField()
    patient_last_name  = serializers.CharField()
    mrn                = serializers.CharField()
    medication_name    = serializers.CharField()
    primary_diagnosis  = serializers.CharField()

    # ── 选填字段（source= 完成字段名映射，validated_data 里直接是新名字）──
    referring_provider_npi = serializers.CharField(
        source='npi', required=False, allow_blank=True, default=''
    )
    referring_provider = serializers.CharField(
        source='provider_name', required=False, allow_blank=True, default=''
    )
    date_of_birth        = serializers.DateField(required=False, allow_null=True, default=None)
    confirm              = serializers.BooleanField(required=False, default=False)
    additional_diagnoses = serializers.CharField(required=False, allow_blank=True, default='')
    medication_history   = serializers.CharField(required=False, allow_blank=True, default='')
    patient_records      = serializers.CharField(required=False, allow_blank=True, default='')

    # ── 字段级校验 ──────────────────────────────────────────────────────────
    def validate_patient_first_name(self, value):
        if not re.fullmatch(r'[A-Za-z ]+', value.strip()):
            raise serializers.ValidationError('Only letters and spaces are allowed.')
        return value.strip()

    def validate_patient_last_name(self, value):
        if not re.fullmatch(r'[A-Za-z ]+', value.strip()):
            raise serializers.ValidationError('Only letters and spaces are allowed.')
        return value.strip()

    def validate_mrn(self, value):
        if not re.fullmatch(r'\d{6}', value):
            raise serializers.ValidationError('MRN must be exactly 6 digits.')
        return value

    def validate_primary_diagnosis(self, value):
        if not re.fullmatch(r'[A-Za-z]\d{2}(\.[A-Za-z0-9]+)?', value.strip()):
            raise serializers.ValidationError(
                'Must be a valid ICD-10 code (e.g. G70.01, I10).'
            )
        return value.strip()

    def validate_referring_provider_npi(self, value):
        if value and not re.fullmatch(r'\d{10}', value):
            raise serializers.ValidationError('NPI must be exactly 10 digits.')
        return value

    # ── 跨字段校验 ──────────────────────────────────────────────────────────
    def validate(self, data):
        # 此时 data 的 key 已经是 source 名（npi / provider_name）
        if data.get('npi') and not data.get('provider_name'):
            raise serializers.ValidationError(
                {'referring_provider': 'Provider name is required when NPI is provided.'}
            )
        return data


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
