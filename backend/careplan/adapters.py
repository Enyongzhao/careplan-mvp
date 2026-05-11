import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class InternalOrder:
    patient_first_name: str = ""
    patient_last_name: str = ""
    mrn: str = ""
    date_of_birth: str = ""
    medication_name: str = ""
    primary_diagnosis: str = ""
    additional_diagnoses: str = ""
    medication_history: str = ""
    provider_name: str = ""
    npi: str = ""
    confirm: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


class BaseIntakeAdapter(ABC):
    def __init__(self):
        self._raw = None

    def parse(self, raw_data) -> "BaseIntakeAdapter":
        self._raw = raw_data
        return self

    @abstractmethod
    def transform(self) -> InternalOrder:
        pass

    def validate(self) -> list[str]:
        # 不调 transform，直接检查 self._order
        if self._order is None:
            return ['transform() must be called first']
        required = (
            'patient_first_name',
            'patient_last_name',
            'mrn',
            'medication_name',
            'primary_diagnosis',
        )
        return [f'{f} is required' for f in required if not getattr(self._order, f, '')]
    
    def ingest(self, raw_data) -> InternalOrder:
        self.parse(raw_data)
        self._order = self.transform()  # 先 transform，存起来
        errors = self.validate()         # validate 用 self._order
        if errors:
            raise ValueError(f"Validation failed: {errors}")
        return self._order


class WebFormAdapter(BaseIntakeAdapter):
    def transform(self) -> InternalOrder:
        d = self._raw
        return InternalOrder(
            patient_first_name=d.get("patient_first_name", ""),
            patient_last_name=d.get("patient_last_name", ""),
            mrn=d.get("mrn", ""),
            date_of_birth=d.get("date_of_birth", ""),
            medication_name=d.get("medication_name", ""),
            primary_diagnosis=d.get("primary_diagnosis", ""),
            additional_diagnoses=d.get("additional_diagnoses", ""),
            medication_history=d.get("medication_history", ""),
            provider_name=d.get("provider_name", ""),
            npi=d.get("npi", ""),
            confirm=d.get("confirm", False),
        )


class ClinicAdapter(BaseIntakeAdapter):
    def transform(self) -> InternalOrder:
        d = self._raw
        return InternalOrder(
            patient_first_name=d.get("fname", ""),
            patient_last_name=d.get("lname", ""),
            mrn=d.get("patient_id", ""),
            medication_name=d.get("drug", ""),
            primary_diagnosis=d.get("dx_code", ""),
            medication_history=d.get("notes", ""),
        )


class PharmCorpAdapter(BaseIntakeAdapter):
    def transform(self) -> InternalOrder:
        root = ET.fromstring(self._raw)
        return InternalOrder(
            patient_first_name=root.findtext("PatientFirstName", ""),
            patient_last_name=root.findtext("PatientLastName", ""),
            mrn=root.findtext("MRN", ""),
            date_of_birth=root.findtext("DateOfBirth", ""),
            medication_name=root.findtext("MedicationName", ""),
            primary_diagnosis=root.findtext("PrimaryDiagnosis", ""),
            additional_diagnoses=root.findtext("AdditionalDiagnoses", ""),
            medication_history=root.findtext("PatientRecords", ""),
            provider_name=root.findtext("ProviderName", ""),
            npi=root.findtext("NPI", ""),
        )


class HospitalDAdapter(BaseIntakeAdapter):
    def transform(self) -> InternalOrder:
        d = self._raw
        return InternalOrder(
            patient_first_name=d.get("first", ""),
            patient_last_name=d.get("last", ""),
            mrn=d.get("record_num", ""),
            medication_name=d.get("medicine", ""),
            primary_diagnosis=d.get("diagnosis", ""),
            medication_history=d.get("history", ""),
        )


_REGISTRY: dict[str, type[BaseIntakeAdapter]] = {
    "web_form": WebFormAdapter,
    "clinic": ClinicAdapter,
    "pharmacorp": PharmCorpAdapter,
    "hospital_d": HospitalDAdapter,
}


# adapters.py
from .exceptions import BlockError

def get_adapter(source: str) -> BaseIntakeAdapter:
    if source not in _REGISTRY:
        raise BlockError(
            message=f"Unknown intake source: '{source}'.",
            code='unknown_source'
        )
    return _REGISTRY[source]()
