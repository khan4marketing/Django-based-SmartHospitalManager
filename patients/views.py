from django.shortcuts import render
from django.contrib.auth import get_user_model
from users.decorators import patient_required
User = get_user_model()


@patient_required
def patient_dashboard(request):
  previous_disease_display = 'None'

  try:
    patient_profile = request.user.patients
    if patient_profile.previous_disease:
      previous_disease_display = patient_profile.get_previous_disease_display()
  except Exception:
    previous_disease_display = 'None'

  return render(request, 'patients/patient_dashboard.html', {
    'previous_disease_display': previous_disease_display,
  })
