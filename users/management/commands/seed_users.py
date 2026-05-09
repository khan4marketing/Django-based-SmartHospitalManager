import random
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from users.models import Address, Doctors, Patients, Specialty


class Command(BaseCommand):
    help = "Create random demo users: 10 doctors and 10 patients by default."

    def add_arguments(self, parser):
        parser.add_argument("--doctors", type=int, default=10, help="Number of doctors to create")
        parser.add_argument("--patients", type=int, default=10, help="Number of patients to create")
        parser.add_argument(
            "--password",
            type=str,
            default="Pass@123",
            help="Password for all seeded users",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        doctor_count = max(0, options["doctors"])
        patient_count = max(0, options["patients"])
        default_password = options["password"]

        if doctor_count == 0 and patient_count == 0:
            self.stdout.write(self.style.WARNING("Nothing to create. Both counts are 0."))
            return

        users_model = get_user_model()
        specialties = self._ensure_specialties()

        doctors_created = 0
        patients_created = 0

        for i in range(doctor_count):
            user = self._create_user(users_model, role="doctor", index=i + 1, password=default_password)
            Doctors.objects.create(
                user=user,
                specialty=random.choice(specialties),
                bio=self._random_bio(),
            )
            doctors_created += 1

        patient_disease_keys = [choice[0] for choice in Patients.previous_disease_choices]

        for i in range(patient_count):
            user = self._create_user(users_model, role="patient", index=i + 1, password=default_password)
            Patients.objects.create(
                user=user,
                previous_disease=random.choice(patient_disease_keys),
            )
            patients_created += 1

        self.stdout.write(self.style.SUCCESS("Seed complete."))
        self.stdout.write(
            f"Doctors created: {doctors_created} | Patients created: {patients_created}"
        )
        self.stdout.write(f"Default password: {default_password}")

    def _create_user(self, users_model, role, index, password):
        username, email = self._unique_identity(users_model, role=role, index=index)
        first_name = random.choice(["Sabbir", "Nadia", "Ayesha", "Imran", "Tanvir", "Rafi"])
        last_name = random.choice(["Khan", "Rahman", "Akter", "Hossain", "Ahmed", "Islam"])

        address = Address.objects.create(
            address_line=f"House {random.randint(1, 250)}, Road {random.randint(1, 30)}",
            region=random.choice(["Dhaka", "Chattogram", "Rajshahi", "Khulna"]),
            city=random.choice(["Dhaka", "Gazipur", "Sylhet", "Barishal", "Cumilla"]),
            code_postal=str(random.randint(1000, 9999)),
        )

        return users_model.objects.create_user(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
            gender=random.choice(["Male", "Female"]),
            birthday=self._random_birthday(),
            password=password,
            recovery_question="pet_name",
            recovery_answer=make_password("seedanswer"),
            id_address=address,
            is_doctor=(role == "doctor"),
        )

    def _unique_identity(self, users_model, role, index):
        stamp = timezone.now().strftime("%Y%m%d%H%M%S")
        while True:
            suffix = random.randint(1000, 9999)
            username = f"{role}_{stamp}_{index}_{suffix}"
            email = f"{username}@example.com"
            if not users_model.objects.filter(username=username).exists() and not users_model.objects.filter(
                email=email
            ).exists():
                return username, email

    def _ensure_specialties(self):
        defaults = [
            ("Cardiology", "heart_disease", "Heart and cardiovascular care."),
            ("Endocrinology", "diabetes", "Hormone and metabolism care."),
            ("Pulmonology", "asthma", "Lung and breathing care."),
            ("Neurology", "epilepsy", "Brain and nervous system care."),
            ("Orthopedics", "arthritis", "Bones and joints care."),
            ("Nephrology", "chronic_kidney_disease", "Kidney-related care."),
        ]

        specialties = []
        for name, disease_key, description in defaults:
            specialty, _ = Specialty.objects.get_or_create(
                name=name,
                defaults={"disease_key": disease_key, "description": description},
            )
            # Keep disease mapping aligned if specialty existed with old values.
            if specialty.disease_key != disease_key:
                specialty.disease_key = disease_key
                specialty.save(update_fields=["disease_key"])
            specialties.append(specialty)

        return specialties

    def _random_bio(self):
        return random.choice(
            [
                "Experienced clinician focused on compassionate patient care.",
                "Dedicated to evidence-based treatment and patient safety.",
                "Works closely with patients for long-term health outcomes.",
                "Committed to preventive care and clear communication.",
            ]
        )

    def _random_birthday(self):
        start = date(1970, 1, 1)
        end = date(2002, 12, 31)
        days_between = (end - start).days
        return start + timedelta(days=random.randint(0, days_between))
