from django.shortcuts import render
from django.contrib.auth import get_user_model
from users.decorators import patient_required
User = get_user_model()


@patient_required
def patient_dashboard(request):
  return render(request,'patients/patient_dashboard.html')
