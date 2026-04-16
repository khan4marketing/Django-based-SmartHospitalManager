from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0002_status_time_alter_appointment_options_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Appointment',
        ),
        migrations.DeleteModel(
            name='Status',
        ),
        migrations.DeleteModel(
            name='Time',
        ),
    ]