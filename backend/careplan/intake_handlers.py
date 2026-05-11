import xml.etree.ElementTree as ET


def parse_clinic_json(data: dict) -> dict:
    return {
        "patient_first_name": data["fname"],
        "patient_last_name": data["lname"],
        "mrn": data["patient_id"],
        "medication_name": data["drug"],
        "primary_diagnosis": data["dx_code"],
        "patient_records": data["notes"],
    }


def parse_pharmacorp_xml(xml_string: str) -> dict:
    root = ET.fromstring(xml_string)
    return {
        "patient_first_name": root.findtext("PatientFirstName"),
        "patient_last_name": root.findtext("PatientLastName"),
        "mrn": root.findtext("MRN"),
        "medication_name": root.findtext("MedicationName"),
        "primary_diagnosis": root.findtext("PrimaryDiagnosis"),
        "patient_records": root.findtext("PatientRecords"),
    }
