from django.urls import path
from .views import patient_dashboard
from doctors.views import patient_profile
urlpatterns = [
  path('patient_dashboard/', patient_dashboard, name='patient_dashboard'),
  path('patient/profile/', patient_profile, name='patient_profile'),
]