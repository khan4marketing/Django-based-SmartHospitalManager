from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.core.paginator import Paginator
from django.db.models import CharField, Q, Value
from django.db.models.functions import Concat
from datetime import datetime
from django.urls import reverse
from users.models import Doctors, Specialty, Patients
from users.reference_data import ensure_disease_specialty_reference_data
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
  ensure_disease_specialty_reference_data(Specialty, Patients._meta.get_field('diseases').remote_field.model)

  if request.method == 'POST' and request.POST.get('add_reminder'):
    title = request.POST.get('title')
    reminder_date = request.POST.get('date') or None
    note = request.POST.get('note')
    normalized_title = (title or '').strip()
    normalized_note = (note or '').strip()

    if not normalized_title:
      messages.error(request, 'Reminder title is required.')
    else:
      reminder_exists = Reminder.objects.filter(
        user=request.user,
        title__iexact=normalized_title,
        date=reminder_date,
        note__iexact=normalized_note,
      ).exists()

      if reminder_exists:
        messages.error(request, 'Duplicate reminder is not allowed.')
      else:
        Reminder.objects.create(user=request.user, title=normalized_title, date=reminder_date, note=normalized_note)
        messages.success(request, 'Reminder added successfully.')

  patient_profile = Patients.objects.filter(user=request.user).first()
  previous_diseases = []
  if patient_profile:
    previous_diseases = list(patient_profile.diseases.values_list('name', flat=True))

  recommended_doctors = []
  recommended_departments = []

  if patient_profile:
    recommended_departments = list(
      {
        dept
        for disease in patient_profile.diseases.all()
        for dept in [disease.suggested_department, *[specialty.department for specialty in disease.specialties.all()]]
        if dept
      }
    )

    recommendation_pool = _build_doctor_recommendations(patient_profile)
    recommended_doctors = recommendation_pool[:8]
  reminder_queryset = Reminder.objects.filter(user=request.user).order_by('-created_at')
  reminders = []
  seen_reminders = set()

  for reminder in reminder_queryset:
    reminder_key = (
      reminder.title.strip().lower(),
      reminder.date,
      reminder.note.strip().lower(),
    )

    if reminder_key in seen_reminders:
      continue

    seen_reminders.add(reminder_key)
    reminders.append(reminder)

  return render(request, 'patients/patient_dashboard.html', {
    'previous_diseases': previous_diseases,
    'previous_disease_count': len(previous_diseases),
    'reminders': reminders,
    'recommended_doctors': recommended_doctors,
    'recommended_departments': recommended_departments,
  })


def _build_doctor_recommendations(patient_profile):
  disease_specialties = set()

  for disease in patient_profile.diseases.all():
    for specialty in disease.specialties.all():
      disease_specialties.add(specialty.name)

  specialty_lookup = {specialty.name: specialty for specialty in Specialty.objects.filter(name__in=disease_specialties)}
  matching_specialty_ids = {specialty.id for specialty in specialty_lookup.values()}

  doctor_rows = []
  all_doctors = Doctors.objects.select_related('user', 'specialty', 'department').prefetch_related('available_times')

  for doctor in all_doctors:
    score = 0
    reasons = []

    if doctor.specialty_id in matching_specialty_ids:
      score += 5
      reasons.append(f"Matches {doctor.specialty.name}")

    if doctor.online_status:
      score += 1
      reasons.append('Online now')

    score += min(int(doctor.years_of_experience / 5), 3)
    score += min(int(float(doctor.rating or 0)), 5)

    if score > 0:
      doctor_rows.append({
        'username': doctor.user.username,
        'name': doctor.user.get_full_name() or doctor.user.username,
        'profile_image': doctor.user.profile_avatar.url if doctor.user.profile_avatar else '',
        'specialty': doctor.specialty.name,
        'experience': doctor.years_of_experience,
        'rating': float(doctor.rating or 0),
        'times': [time_slot.time for time_slot in doctor.available_times.all()],
        'room': doctor.room_number,
        'online': doctor.online_status,
        'score': score,
        'match_reasons': reasons,
      })

  doctor_rows.sort(key=lambda item: (item['score'], item['online'], item['rating'], item['experience']), reverse=True)

  return doctor_rows


@login_required(login_url='/login')
def profile(request):
  # Redirect doctors to the doctor profile
  if request.user.is_doctor:
    return redirect('doctor_profile')

  updated_profile_successfully  = False
  updated_password_successfully = False

  if request.method == 'POST':
    if 'update_profile' in request.POST:
      user = request.user
      user.first_name = request.POST.get('user_firstname')
      user.last_name = request.POST.get('user_lastname')
      user.gender = request.POST.get('user_gender')
      user.birthday = request.POST.get('birthday')

      # address may be None initially
      if user.id_address:
        user.id_address.address_line = request.POST.get('address_line')
        user.id_address.region = request.POST.get('region')
        user.id_address.city = request.POST.get('city')
        user.id_address.code_postal = request.POST.get('code_postal')
        user.id_address.save()

      if 'profile_pic' in request.FILES:
        user.profile_avatar = request.FILES['profile_pic']

      user.save()
      updated_profile_successfully  = True

    elif 'update_password' in request.POST:
      current_password = request.POST.get('current_password')
      new_password = request.POST.get('new_password')
      confirm_new_password = request.POST.get('confirm_new_password')

      if not request.user.check_password(current_password):
        messages.error(request, 'Incorrect password. Please try again.')
      elif new_password != confirm_new_password:
        messages.error(request, 'New passwords do not match. Please try again.')
      elif len(new_password) < 6:
        messages.error(request, 'New password must be at least 6 characters long.')
      else:
        request.user.set_password(new_password)
        request.user.save()
        update_session_auth_hash(request, request.user) 
        updated_password_successfully = True

  curruser = request.user.username
  data = User.objects.get(username=curruser)

  return render(request, 'patients/profile.html', context={
      'basicdata': data,
      'updated_profile_successfully': updated_profile_successfully,
      'updated_password_successfully': updated_password_successfully,
      'base_template': 'patients/base.html'
  })


@patient_required
def my_appointments(request):
  if request.user.is_doctor:
    messages.error(request, 'Only patient accounts can view appointments.')
    return redirect('doctor_dashboard')

  patient_profile, _ = Patients.objects.get_or_create(user=request.user)

  app = Appointment.objects.filter(patient__user = request.user)
  
  filter_status = request.GET.get('filter_status')
  filter_date = request.GET.get('filter_date')
  filter_doctor_name = request.GET.get('filter_doctor_name')

  if filter_status and filter_status != 'All':
    app = app.filter(status__status=filter_status)

  if filter_date:
    app = app.filter(start_date=filter_date)

  if filter_doctor_name:
    app = app.annotate(
      doctor_full_name=Concat(
        'doctor__user__first_name',
        Value(' '),
        'doctor__user__last_name',
        output_field=CharField(),
      )
    ).filter(
      Q(doctor_full_name__icontains=filter_doctor_name) |
      Q(doctor__user__username__icontains=filter_doctor_name) |
      Q(doctor__user__id_address__city__icontains=filter_doctor_name)
    )

  return render(request, "patients/my_appointments.html", {
    'appointments': app,
    'filter_status': filter_status,
    'filter_date': filter_date,
    'filter_doctor_name': filter_doctor_name
  })
  



@patient_required
def book_appointment(request):
  if request.user.is_doctor:
    messages.error(request, 'Only patient accounts can book appointments.')
    return redirect('doctor_dashboard')

  Patients.objects.get_or_create(user=request.user)
  ensure_appointment_reference_data()

  specialities = Specialty.objects.all()
  doctors = Doctors.objects.all()
  
  filter_speciality = request.GET.get('filter_speciality')

  if filter_speciality and filter_speciality != 'All':
    doctors = doctors.filter(specialty__name=filter_speciality)

  return render(request, "patients/book_appointment.html", {
    'doctors': doctors,
    'specialities': specialities,
    'filter_speciality': filter_speciality,
  })
  
  # return render(request,'patients/book_appointment.html',{"doctors":doctors})


@patient_required
def patient_confirm_book(request , doctor):
  if request.user.is_doctor:
    messages.error(request, 'Only patient accounts can book appointments.')
    return redirect('doctor_dashboard')

  ensure_appointment_reference_data()

  patient_profile, _ = Patients.objects.get_or_create(user=request.user)
  selected_doctor = get_object_or_404(Doctors, user__username=doctor)

  if request.method == 'POST':
    try:
      date = request.POST.get("date")
      summary = request.POST.get("summary")
      description = request.POST.get("description")
      time = request.POST.get("time")

      if not date or not summary or not description or not time:
        messages.error(request, 'Please fill in all appointment details.')
        times = Time.objects.all()
        return render(request, 'patients/patient_confirm_book.html', {
          'times': times,
          'doctor': selected_doctor,
          'summary': summary,
          'description': description,
          'date': date,
        })

      try:
        parsed_date = datetime.strptime(date, '%Y-%m-%d').date()
      except Exception:
        messages.error(request, 'Invalid date format. Please use YYYY-MM-DD.')
        times = Time.objects.all()
        return render(request, 'patients/patient_confirm_book.html', {
          'times': times,
          'doctor': selected_doctor,
          'summary': summary,
          'description': description,
          'date': date,
        })

      heure, _ = Time.objects.get_or_create(time=time)
      doctor_obj = selected_doctor
      status, _ = Status.objects.get_or_create(status="Waited")

      Appointment.objects.create(
        summary=summary,
        description=description,
        start_date=parsed_date,
        time=heure,
        doctor=doctor_obj,
        patient=patient_profile,
        status=status,
      )

      messages.success(request, 'Appointment booked successfully.')
      return redirect('my_appointments')

    except Exception as e:
      messages.error(request, f"Could not create appointment: {e}")
      times = Time.objects.all()
      return render(request, 'patients/patient_confirm_book.html', {
        'times': times,
        'doctor': selected_doctor,
        'summary': request.POST.get('summary', ''),
        'description': request.POST.get('description', ''),
        'date': request.POST.get('date', ''),
      })

  times = Time.objects.all()
  return render(request, 'patients/patient_confirm_book.html', {
    'times': times,
    'doctor': selected_doctor,
    'summary': '',
    'description': '',
    'date': '',
  })
