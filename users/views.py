from django.shortcuts import render

from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import Doctors, Patients, Address, Specialty


Users = get_user_model()

def csrf_failure(request, reason=""):
  # Tokens can become stale after login/logout in another tab.
  messages.error(request, 'Your session token expired. Please reload the page and submit again.')
  return redirect(request.path)


@ensure_csrf_cookie
def register(request):
  specialties = Specialty.objects.all().order_by('name')

  if request.method == 'POST':
    user_status = request.POST.get('user_config')
    first_name = request.POST.get('user_firstname')
    last_name = request.POST.get('user_lastname')
    profile_pic = ""

    if "profile_pic" in request.FILES:
      profile_pic = request.FILES['profile_pic']

    username = request.POST.get('user_id')
    email = request.POST.get('email')
    gender = request.POST.get('user_gender')
    birthday = request.POST.get("birthday")
    password = request.POST.get('password')
    confirm_password = request.POST.get('conf_password')
    recovery_question = request.POST.get('recovery_question')
    recovery_answer = (request.POST.get('recovery_answer') or '').strip().lower()
    address_line = request.POST.get('address_line')
    region = request.POST.get('region')
    city = request.POST.get('city')
    pincode = request.POST.get('pincode')
    previous_disease = request.POST.get('previous_disease')

    form_context = {
      'user_config': user_status,
      'user_firstname': first_name,
      'user_lastname': last_name,
      'user_id': username,
      'email': email,
      'user_gender': gender,
      'birthday': birthday,
      'address_line': address_line,
      'region': region,
      'city': city,
      'pincode': pincode,
      'previous_disease': previous_disease,
      'specialty': request.POST.get('specialty'),
      'bio': request.POST.get('bio'),
      'recovery_question': recovery_question,
      'specialties': specialties,
    }

    if len(password) < 6:
      messages.error(request, 'Password must be at least 6 characters long.')
      return render(request, 'users/register.html', context=form_context)

    if password != confirm_password:
      messages.error(request, 'Passwords do not match.')
      return render(request, 'users/register.html', context=form_context)

    if not recovery_question or not recovery_answer:
      messages.error(request, 'Security question and answer are required.')
      return render(request, 'users/register.html', context=form_context)

    if Users.objects.filter(username=username).exists():
      messages.error(request, 'Username already exists. Try again with a different username.')
      return render(request, 'users/register.html', context=form_context)

    address = Address.objects.create(address_line=address_line, region=region,city=city, code_postal=pincode)

    user = Users.objects.create_user(
      first_name=first_name,
      last_name=last_name,
      profile_avatar=profile_pic,
      username=username,
      email=email,
      gender=gender,
      birthday=birthday,
      password=password,
      recovery_question=recovery_question,
      recovery_answer=make_password(recovery_answer),
      id_address=address,
      is_doctor=(user_status == 'Doctor')
    )
      
    user.save()

    if user_status == 'Doctor':
      specialty_id = (request.POST.get('specialty') or '').strip()
      if not specialty_id:
        messages.error(request, 'Specialty is required for doctors.')
        return render(request, 'users/register.html', context=form_context)

      specialty_obj = Specialty.objects.filter(id=specialty_id).first()
      if not specialty_obj:
        messages.error(request, 'Please select a valid specialty for doctors.')
        return render(request, 'users/register.html', context=form_context)

      bio = request.POST.get('bio')
      doctor = Doctors.objects.create(user=user, specialty=specialty_obj, bio=bio)
      doctor.save()
        
    elif user_status == 'Patient':
        if not previous_disease:
          messages.error(request, 'Previous disease is required for patients.')
          return render(request, 'users/register.html', context=form_context)
        patient = Patients.objects.create(user=user, previous_disease=previous_disease)
        patient.save()

    messages.success(request, 'Your account has been successfully registered. Please login.', extra_tags='success')
    return redirect('login')


  return render(request, 'users/register.html', {'specialties': specialties})


@ensure_csrf_cookie
def login_view(request):
  if request.method == 'POST':
    username = request.POST.get('username')
    password = request.POST.get('password')
    user_config = request.POST.get('user_config')

    user = authenticate(request, username=username, password=password)

    if user is not None:
      if user_config == 'Doctor' and not user.is_doctor:
        messages.error(request, 'This account is not registered as a doctor.')
        return render(request, 'users/login.html', {'selected_user_config': user_config})

      if user_config == 'Patient' and user.is_doctor:
        messages.error(request, 'This account is not registered as a patient.')
        return render(request, 'users/login.html', {'selected_user_config': user_config})

      login(request, user)

      if user.is_doctor:
        return redirect('doctor_dashboard')

      if Patients.objects.filter(user=user).exists():
        return redirect('patient_dashboard')

      # Fallback: if a non-doctor user exists without a Patient row,
      # still move forward instead of staying on the login page.
      return redirect('patient_dashboard')
    else:
      messages.error(request, 'Incorrect username or password')
      
    return render(request, 'users/login.html', {'selected_user_config': user_config})
  
  return render(request, 'users/login.html')


@ensure_csrf_cookie
def forgot_view(request):
    if request.method == 'POST':
        step = request.POST.get('step', 'lookup')

        if step == 'lookup':
            username = (request.POST.get('username') or '').strip()
            user = Users.objects.filter(username=username).first()

            if not user:
                messages.error(request, 'Username not found.')
                return render(request, 'users/forgot.html')

            if not user.recovery_question or not user.recovery_answer:
                messages.error(request, 'Security key is not configured for this account.')
                return render(request, 'users/forgot.html')

            return render(request, 'users/forgot.html', context={
                'step': 'verify',
                'username': user.username,
                'recovery_question': user.get_recovery_question_display(),
            })

        if step == 'verify':
            username = (request.POST.get('username') or '').strip()
            answer = (request.POST.get('recovery_answer') or '').strip().lower()
            password = request.POST.get('password')
            confirm_password = request.POST.get('conf_password')
            user = Users.objects.filter(username=username).first()

            if not user:
                messages.error(request, 'Username not found.')
                return render(request, 'users/forgot.html')

            if not check_password(answer, user.recovery_answer):
                messages.error(request, 'Security answer is incorrect.')
                return render(request, 'users/forgot.html', context={
                    'step': 'verify',
                    'username': user.username,
                    'recovery_question': user.get_recovery_question_display(),
                })

            if len(password) < 6:
                messages.error(request, 'Password must be at least 6 characters long.')
                return render(request, 'users/forgot.html', context={
                    'step': 'verify',
                    'username': user.username,
                    'recovery_question': user.get_recovery_question_display(),
                })

            if password != confirm_password:
                messages.error(request, 'Passwords do not match.')
                return render(request, 'users/forgot.html', context={
                    'step': 'verify',
                    'username': user.username,
                    'recovery_question': user.get_recovery_question_display(),
                })

            user.set_password(password)
            user.save()
            messages.success(request, 'Password reset successful. Please login.', extra_tags='success')
            return redirect('login')

    return render(request, 'users/forgot.html')
@login_required(login_url='/login')
def logout_view(request):
    logout(request)
    return redirect('login')


def member_auth_view(request, member_id, page_type):
  member_template_map = {
    '23303189': 'id1',
    '23303152': 'id2',
    '2330358': 'id3',
    '23303162': 'id4',
    '23303163': 'id5',
  }
  allowed_pages = {'login', 'register'}

  if member_id not in member_template_map or page_type not in allowed_pages:
    return redirect('login')

  template_member_id = member_template_map[member_id]

  return render(request, f'users/member_auth/{page_type}-{template_member_id}.html', {
    'member_id': member_id,
    'page_type': page_type,
    'switch_login_url_name': f'login-{member_id}',
    'switch_register_url_name': f'register-{member_id}',
  })
