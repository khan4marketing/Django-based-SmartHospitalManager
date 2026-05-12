from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.core.paginator import Paginator
from django.db.models import Q
from datetime import datetime
from django.urls import reverse
from users.models import Doctors , Specialty , Patients
from patients.models import Appointment , Time , Status, Reminder

User = get_user_model()


@login_required(login_url='/login')
def patient_dashboard(request):
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

  # Recommendation logic
  recommended_doctors = []
  recommended_departments = []

  if patient_profile:
    # derive specialties from known diseases
    disease_specialties = set()
    disease_departments = set()
    for d in patient_profile.diseases.all():
      for s in d.specialties.all():
        disease_specialties.add(s.name)
        if s.department:
          disease_departments.add(s.department)
      if d.suggested_department:
        disease_departments.add(d.suggested_department)

    # simple symptom-to-specialty mapping
    symptoms_text = (patient_profile.current_symptoms or '').lower()
    symptom_map = {
      'chest': 'Cardiologist',
      'pain': 'Cardiologist',
      'fever': 'Physician',
      'cough': 'Physician',
      'skin': 'Dermatologist',
      'rash': 'Dermatologist',
      'eye': 'Ophthalmologist',
      'vision': 'Ophthalmologist',
      'depress': 'Psychiatrist',
      'anxiet': 'Psychiatrist',
      'diabet': 'Endocrinologist',
      'kidney': 'Nephrologist'
    }

    for k, spec in symptom_map.items():
      if k in symptoms_text:
        disease_specialties.add(spec)

    # Age based suggestions (example thresholds)
    if patient_profile.age:
      age = patient_profile.age
      if age >= 60:
        disease_specialties.add('Geriatrician')
      if age <= 12:
        disease_specialties.add('Pediatrician')

    # collect specialty objects
    preferred_specialties = Specialty.objects.filter(name__in=list(disease_specialties))

    # departments from specialties
    for s in preferred_specialties:
      if s.department:
        disease_departments.add(s.department)

    recommended_departments = list(disease_departments)

    # find matching doctors, prioritize available and highly rated
    doctors_qs = Doctors.objects.none()
    if preferred_specialties.exists():
      doctors_qs = Doctors.objects.filter(specialty__in=preferred_specialties).order_by('-online_status','-rating','-years_of_experience')
    else:
      # fallback to general physicians
      doctors_qs = Doctors.objects.filter(specialty__name__in=['Physician','General Medicine']).order_by('-online_status','-rating','-years_of_experience')

    # build a lightweight structure for template
    for doc in doctors_qs[:8]:
      times = [t.time for t in doc.available_times.all()]
      recommended_doctors.append({
        'username': doc.user.username,
        'name': doc.user.get_full_name() or doc.user.username,
        'profile_image': doc.user.profile_avatar.url if doc.user.profile_avatar else '',
        'specialty': doc.specialty.name,
        'experience': doc.years_of_experience,
        'rating': float(doc.rating or 0),
        'times': times,
        'room': doc.room_number,
        'online': doc.online_status,
      })
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


@login_required(login_url='/login')
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
    app = app.filter(doctor__user__first_name__icontains=filter_doctor_name)

  return render(request, "patients/my_appointments.html", {
    'appointments': app,
    'filter_status': filter_status,
    'filter_date': filter_date,
    'filter_doctor_name': filter_doctor_name
  })
  



@login_required(login_url='/login')
def book_appointment(request):
  if request.user.is_doctor:
    messages.error(request, 'Only patient accounts can book appointments.')
    return redirect('doctor_dashboard')

  Patients.objects.get_or_create(user=request.user)

  specialities = Specialty.objects.all()
  doctors = Doctors.objects.all()
  
  filter_speciality = request.GET.get('filter_speciality')
  filter_doctor_name = request.GET.get('filter_doctor_name')

  if filter_speciality and filter_speciality != 'All':
    doctors = doctors.filter(specialty__name=filter_speciality)

  if filter_doctor_name:
    doctors = doctors.filter(
      Q(user__first_name__icontains=filter_doctor_name) |
      Q(user__last_name__icontains=filter_doctor_name) |
      Q(user__username__icontains=filter_doctor_name)
    )

  return render(request, "patients/book_appointment.html", {
    'doctors': doctors,
    'specialities': specialities,
    'filter_speciality': filter_speciality,
    'filter_doctor_name': filter_doctor_name,
  })
  
  # return render(request,'patients/book_appointment.html',{"doctors":doctors})


@login_required(login_url='/login')
def patient_confirm_book(request , doctor):
  if request.user.is_doctor:
    messages.error(request, 'Only patient accounts can book appointments.')
    return redirect('doctor_dashboard')

  patient_profile, _ = Patients.objects.get_or_create(user=request.user)

  selected_doctor = get_object_or_404(Doctors, user__username=doctor)

  if request.method == 'POST':
    date = request.POST.get("date")
    summary = request.POST.get("summary")
    description = request.POST.get("description")
    time = request.POST.get("time")
    heure = get_object_or_404(Time, time=time)
    status = get_object_or_404(Status, status="Waited")

    if not date or not summary or not description:
      messages.error(request, 'Please fill in all appointment details.')
      times = Time.objects.all()
      return render(request, 'patients/patient_confirm_book.html', {'times': times, 'doctor': selected_doctor})
    
    appointment = Appointment.objects.create(
      summary=summary,
      description=description,
      start_date=date,
      time=heure,
      doctor=selected_doctor,
      patient=patient_profile,
      status = status
    )
    
    if appointment:
      messages.success(request, 'Appointment booked successfully.')
      return redirect('my_appointments')
    
  times = Time.objects.all()
  return render(request, 'patients/patient_confirm_book.html', {'times': times, 'doctor': selected_doctor})
