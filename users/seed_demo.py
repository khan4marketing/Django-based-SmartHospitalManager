import random
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from users.models import Address, Doctors, Disease, Patients, Specialty
from users.reference_data import DISEASE_SPECIALTY_MAP, ensure_disease_specialty_reference_data


DOCTOR_FIRST_NAMES = [
    'Ayaan',
    'Sabbir',
    'Nadia',
    'Imran',
    'Tanvir',
    'Rafi',
    'Nusrat',
    'Jannat',
    'Farhan',
    'Tania',
    'Mahir',
    'Arif',
    'Shaila',
    'Rahat',
    'Sakib',
    'Maliha',
    'Fahim',
    'Tanjina',
    'Asif',
    'Hafsa',
]

LAST_NAMES = [
    'Khan',
    'Rahman',
    'Akter',
    'Hossain',
    'Ahmed',
    'Islam',
    'Chowdhury',
    'Sarker',
    'Haque',
    'Miah',
    'Amin',
    'Uddin',
    'Das',
    'Bhuiyan',
    'Paul',
    'Talukder',
    'Jahan',
    'Rana',
    'Ferdous',
    'Sultana',
]

DOCTOR_BIOS = [
    'Experienced clinician focused on compassionate patient care.',
    'Dedicated to evidence-based treatment and patient safety.',
    'Works closely with patients for long-term health outcomes.',
    'Committed to preventive care and clear communication.',
]

PATIENT_SYMPTOMS = [
    'Fever and fatigue',
    'Joint pain and stiffness',
    'Headache and dizziness',
    'Breathing discomfort',
    'Stomach pain and nausea',
    'Vision blur and eye strain',
    'Anxiety and sleep disturbance',
    'Back pain and swelling',
]

BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']


def seed_demo_data(doctor_count=20, patient_count=20, password='Pass@123', skip_if_seeded=False):
    users_model = get_user_model()

    if skip_if_seeded and (Doctors.objects.exists() or Patients.objects.exists()):
        return {'doctors_created': 0, 'patients_created': 0, 'skipped': True}

    specialties = _ensure_reference_data()
    created_doctors = 0
    created_patients = 0

    with transaction.atomic():
        for index in range(doctor_count):
            user = _create_user(users_model, role='doctor', index=index + 1, password=password)
            Doctors.objects.create(
                user=user,
                specialty=random.choice(specialties),
                bio=random.choice(DOCTOR_BIOS),
                years_of_experience=random.randint(1, 25),
                rating=Decimal(str(round(random.uniform(4.0, 5.0), 1))),
                room_number=f'R-{random.randint(101, 520)}',
                online_status=random.choice([True, False]),
            )
            created_doctors += 1

        disease_pool = list(Disease.objects.all())
        if not disease_pool:
            _ensure_reference_data()
            disease_pool = list(Disease.objects.all())

        for index in range(patient_count):
            user = _create_user(users_model, role='patient', index=index + 1, password=password)
            patient = Patients.objects.create(
                user=user,
                age=random.randint(6, 82),
                blood_group=random.choice(BLOOD_GROUPS),
                emergency_contact=f'+8801{random.randint(30000000, 99999999)}',
                current_symptoms=random.choice(PATIENT_SYMPTOMS),
                medical_history_summary='',
            )
            selected_diseases = random.sample(disease_pool, k=random.randint(1, min(3, len(disease_pool))))
            patient.diseases.set(selected_diseases)
            patient.medical_history_summary = ', '.join(disease.name for disease in selected_diseases)
            patient.save(update_fields=['medical_history_summary'])
            created_patients += 1

    return {
        'doctors_created': created_doctors,
        'patients_created': created_patients,
        'skipped': False,
    }


def _create_user(users_model, role, index, password):
    username, email = _unique_identity(users_model, role=role, index=index)
    first_name = random.choice(DOCTOR_FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)

    address = Address.objects.create(
        address_line=f'House {random.randint(1, 250)}, Road {random.randint(1, 40)}',
        region=random.choice(['Dhaka', 'Chattogram', 'Rajshahi', 'Khulna', 'Sylhet']),
        city=random.choice(['Dhaka', 'Gazipur', 'Cumilla', 'Barishal', 'Narayanganj']),
        code_postal=str(random.randint(1000, 9999)),
    )

    return users_model.objects.create_user(
        first_name=first_name,
        last_name=last_name,
        username=username,
        email=email,
        gender=random.choice(['Male', 'Female']),
        birthday=_random_birthday(),
        password=password,
        id_address=address,
        is_doctor=(role == 'doctor'),
    )


def _unique_identity(users_model, role, index):
    stamp = timezone.now().strftime('%Y%m%d%H%M%S')
    while True:
        suffix = random.randint(1000, 9999)
        username = f'{role}_{stamp}_{index}_{suffix}'
        email = f'{username}@example.com'
        if not users_model.objects.filter(username=username).exists() and not users_model.objects.filter(email=email).exists():
            return username, email


def _ensure_reference_data():
    ensure_disease_specialty_reference_data(Specialty, Disease)
    return list(Specialty.objects.all().order_by('name'))


def _random_birthday():
    start = date(1970, 1, 1)
    end = date(2004, 12, 31)
    days_between = (end - start).days
    return start + timedelta(days=random.randint(0, days_between))