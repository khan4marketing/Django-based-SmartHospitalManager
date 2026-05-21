from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from users.seed_demo import seed_demo_data


class Command(BaseCommand):
    help = "Create random demo users: 20 doctors and 20 patients by default."

    def add_arguments(self, parser):
        parser.add_argument("--doctors", type=int, default=20, help="Number of doctors to create")
        parser.add_argument("--patients", type=int, default=20, help="Number of patients to create")
        parser.add_argument(
            "--password",
            type=str,
            default="Pass@123",
            help="Password for all seeded users",
        )

    def handle(self, *args, **options):
        doctor_count = max(0, options["doctors"])
        patient_count = max(0, options["patients"])
        default_password = options["password"]

        if doctor_count == 0 and patient_count == 0:
            self.stdout.write(self.style.WARNING("Nothing to create. Both counts are 0."))
            return

        result = seed_demo_data(
            doctor_count=doctor_count,
            patient_count=patient_count,
            password=default_password,
            skip_if_seeded=False,
        )

        self.stdout.write(self.style.SUCCESS("Seed complete."))
        self.stdout.write(
            f"Doctors created: {result['doctors_created']} | Patients created: {result['patients_created']}"
        )
        self.stdout.write(f"Default password: {default_password}")
