from django.apps import AppConfig
from django.conf import settings


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(self):
        from django.db.models.signals import post_migrate

        from .seed_demo import seed_demo_data

        def bootstrap_demo_data(sender, **kwargs):
            if sender.label != 'users':
                return

            if not getattr(settings, 'AUTO_SEED_DEMO_DATA', True):
                return

            seed_demo_data(doctor_count=20, patient_count=20, password='Pass@123', skip_if_seeded=True)

        post_migrate.connect(bootstrap_demo_data, dispatch_uid='users.bootstrap_demo_data')
