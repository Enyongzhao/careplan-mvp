import uuid
from django.db import models


class Patient(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    mrn = models.CharField(max_length=50, unique=True)
    date_of_birth = models.DateField(null=True, blank=True)


class Provider(models.Model):
    name = models.CharField(max_length=200)
    npi = models.CharField(max_length=20, unique=True)


class Order(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    provider = models.ForeignKey(Provider, on_delete=models.SET_NULL, null=True)
    medication_name = models.CharField(max_length=200)
    primary_diagnosis = models.TextField()
    additional_diagnoses = models.TextField(blank=True, default='')
    medication_history = models.TextField(blank=True, default='')
    patient_records = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)


class CarePlan(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='careplan')
    content = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
