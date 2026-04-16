from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from users.decorators import doctor_required, patient_required

from users.models import Doctors, Specialty

User = get_user_model()

@doctor_required
def doctor_dashboard(request):
  return render(request, 'doctors/doctor_dashboard.html')

def _profile(request):
    updated_profile_successfully  = False
    updated_password_successfully = False
    base_template = 'patients/base.html'
    if request.user.is_doctor:
      base_template = 'doctors/base.html'
    
    if request.method == 'POST':
      if 'update_profile' in request.POST:
        user = request.user
        user.first_name = request.POST.get('user_firstname')
        user.last_name = request.POST.get('user_lastname')
        user.gender = request.POST.get('user_gender')
        user.birthday = request.POST.get('birthday')
        user.id_address.address_line = request.POST.get('address_line')
        user.id_address.region = request.POST.get('region')
        user.id_address.city = request.POST.get('city')
        user.id_address.code_postal = request.POST.get('code_postal')
        
        if(user.is_doctor):
          specialty = (request.POST.get('specialty') or request.POST.get('Speciality') or '').strip()
          if not specialty:
            messages.error(request, 'Specialty is required for doctors.')
          else:
            specialty_name, _ = Specialty.objects.get_or_create(
              name=specialty,
              defaults={'description': ''}
            )

            doctor_profile = user.doctors
            doctor_profile.specialty = specialty_name
            doctor_profile.bio = request.POST.get('bio')
            doctor_profile.save()
        else:
          patient_profile = user.patients
          patient_profile.insurance = request.POST.get('insurance')
          patient_profile.save()



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
    return render(request, 'doctors/profile.html', context={
            "basicdata": data,
            "updated_profile_successfully": updated_profile_successfully,
            "updated_password_successfully": updated_password_successfully,
            'base_template': base_template,
        })


@doctor_required
def doctor_profile(request):
    return _profile(request)


@patient_required
def patient_profile(request):
    return _profile(request)
    

