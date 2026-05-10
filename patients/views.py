from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.core.paginator import Paginator
from datetime import datetime
from django.urls import reverse
from users.models import Doctors , Specialty , Patients
from users.decorators import patient_required
from patients.models import Appointment , Time , Status, Reminder
from django.contrib import messages

def ensure_appointment_reference_data():
  # create some default time slots and statuses if the tables are empty
  if Time.objects.count() == 0:
    default_times = [
      '08:00', '08:30', '09:00', '09:30', '10:00', '10:30',
      '11:00', '11:30', '12:00', '13:00', '14:00', '15:00',
      '16:00', '16:30', '17:00'
    ]
    for t in default_times:
      Time.objects.get_or_create(time=t)
  if Status.objects.count() == 0:
    default_status = ['Waited', 'Accepted', 'Cancelled', 'Completed']
    for s in default_status:
      Status.objects.get_or_create(status=s)

User = get_user_model()


@patient_required
def patient_dashboard(request):
  if request.method == 'POST' and request.POST.get('add_reminder'):
    title = request.POST.get('title')
    date = request.POST.get('date') or None
    note = request.POST.get('note')
    Reminder.objects.create(user=request.user, title=title, date=date, note=note)

  patient_profile = Patients.objects.filter(user=request.user).first()
  previous_diseases = []
  if patient_profile:
    previous_diseases = list(patient_profile.diseases.values_list('name', flat=True))

  reminders = Reminder.objects.filter(user=request.user).order_by('-created_at')

  return render(request, 'patients/patient_dashboard.html', {
    'previous_diseases': previous_diseases,
    'previous_disease_count': len(previous_diseases),
    'reminders': reminders,
  })


@patient_required
def my_appointments(request):
  app = Appointment.objects.filter(patient__user = request.user)
  
  filter_status = request.GET.get('filter_status')
  filter_date = request.GET.get('filter_date')
  filter_doctor_name = request.GET.get('filter_doctor_name')

  if filter_status and filter_status != 'All':
    app = app.filter(status__status=filter_status)

  if filter_date:
    app = app.filter(start_date=filter_date)

  if filter_doctor_name:
    app = app.filter(doctor__user__first_name__icontains=filter_doctor_name)

  return render(request, "patients/my_appointments.html", {
    'appointments': app,
    'filter_status': filter_status,
    'filter_date': filter_date,
    'filter_doctor_name': filter_doctor_name
  })
  



@patient_required
def book_appointment(request):
  ensure_appointment_reference_data()
  specialities = Specialty.objects.all()
  doctors = Doctors.objects.all()
  
  filter_speciality = request.GET.get('filter_speciality')
  filter_city = request.GET.get('filter_city')
  filter_doctor_name = request.GET.get('filter_doctor_name')

  if filter_speciality and filter_speciality != 'All':
    doctors = doctors.filter(specialty__name=filter_speciality)

  if filter_doctor_name:
    doctors = doctors.filter(user__first_name__icontains=filter_doctor_name)

  if filter_city:
    doctors = doctors.filter(user__id_address__city__icontains=filter_city)

  return render(request, "patients/book_appointment.html", {
    'doctors': doctors,
    'specialities': specialities,
    'filter_speciality': filter_speciality,
    'filter_doctor_name': filter_doctor_name,
    'filter_city': filter_city,
  })
  
  # return render(request,'patients/book_appointment.html',{"doctors":doctors})


@patient_required
def patient_confirm_book(request , doctor):
  print(doctor)
  # ensure reference data (time slots, statuses) exist so the booking form can render
  ensure_appointment_reference_data()
  if request.method == 'POST':
    try:
      date = request.POST.get("date")
      summary = request.POST.get("summary")
      description = request.POST.get("description")
      time = request.POST.get("time")

      # validate required fields so browsers with no native date picker still work
      if not date or date == 'None':
        messages.error(request, 'Please select a valid date for the appointment.')
        doc = Doctors.objects.get(user__username=doctor)
        times = Time.objects.all()
        return render(request,'patients/patient_confirm_book.html' ,{'times':times ,'doctor': doc, 'summary': summary, 'description': description, 'date': date})

      # parse date safely
      try:
        parsed_date = datetime.strptime(date, '%Y-%m-%d').date()
      except Exception:
        messages.error(request, 'Invalid date format. Please use YYYY-MM-DD.')
        doc = Doctors.objects.get(user__username=doctor)
        times = Time.objects.all()
        return render(request,'patients/patient_confirm_book.html' ,{'times':times ,'doctor': doc, 'summary': summary, 'description': description, 'date': date})

      # tolerate missing reference rows by creating them on-demand
      heure, _ = Time.objects.get_or_create(time=time)
      doctor_obj = Doctors.objects.get(user__username = doctor)
      patient = Patients.objects.get(user=request.user)
      status, _ = Status.objects.get_or_create(status="Waited")

      appointment = Appointment.objects.create(
        summary=summary,
        description=description,
        start_date=parsed_date,
        time=heure,
        doctor=doctor_obj,
        patient=patient,
        status = status
      )

      if appointment:
        app = Appointment.objects.filter(patient__user = request.user)
        return render(request,'patients/my_appointments.html',{"appointments":app})

    except Exception as e:
      messages.error(request, f"Could not create appointment: {e}")
      doc = Doctors.objects.get(user__username=doctor)
      times = Time.objects.all()
      return render(request,'patients/patient_confirm_book.html' ,{'times':times ,'doctor': doc, 'summary': request.POST.get('summary',''), 'description': request.POST.get('description',''), 'date': request.POST.get('date','')})
    
    
  doc = Doctors.objects.get(user__username=doctor)
  if doc:
    times = Time.objects.all()
    return render(request,'patients/patient_confirm_book.html' ,{'times':times ,'doctor': doc, 'summary': '', 'description': '', 'date': '' })
  
  doctors = Doctors.objects.all()
  return render(request,'patients/book_appointment.html',{"doctors":doctors})
