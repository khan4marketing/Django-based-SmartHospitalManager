from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission


class Department(models.Model):
    name = models.CharField(max_length=80, unique=True)
    description = models.TextField(blank=True)
    icon_class = models.CharField(max_length=80, blank=True)
    is_emergency = models.BooleanField(default=False)

    class Meta:
      verbose_name = "Department"
      verbose_name_plural = "Departments"

    def __str__(self):
      return self.name


class Address(models.Model):
    id_address = models.AutoField(primary_key=True)
    address_line = models.CharField(max_length=50)
    region = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    code_postal = models.CharField(max_length=50)
    
    class Meta:
      verbose_name = "Address"
      verbose_name_plural = "Addresses"
      
    def __str__(self):
      return self.address_line


class Users(AbstractUser):
    email = models.CharField(max_length=50, unique=True)
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=200)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=20, blank=True)
    gender_choices = (("Male", "Male"), ("Female", "Female"))
    gender = models.CharField(max_length=10, choices=gender_choices, default="not_known")
    birthday = models.DateField(null=True, blank=True)
    is_doctor = models.BooleanField(default=False)
    profile_avatar = models.ImageField(upload_to="users/profiles", blank=True, default="doctor/profiles/download.png")
    id_address = models.ForeignKey(Address, on_delete=models.CASCADE, null=True)
    
    class Meta:
      verbose_name = "User"
      verbose_name_plural = "Users"
      
    def __str__(self):
      return self.username


class Reste_token(models.Model):
   user = models.ForeignKey(Users, on_delete=models.CASCADE)
   email = models.CharField(max_length=50, unique=True)
   token = models.CharField(max_length=50)


class Specialty(models.Model):
    name = models.CharField(max_length=25, unique=True)
    description = models.TextField()
    # optional key to keep mapping to seed data
    disease_key = models.CharField(max_length=50, blank=True, null=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='specialties')

    class Meta:
        verbose_name = "Specialty"
        verbose_name_plural = "Specialty"

    def __str__(self):
        return self.name


class Disease(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    specialties = models.ManyToManyField(Specialty, related_name='diseases', blank=True)
    suggested_department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='diseases')

    class Meta:
        verbose_name = "Disease"
        verbose_name_plural = "Diseases"

    def __str__(self):
        return self.name
    

class Doctors(models.Model):
  user = models.OneToOneField(Users, on_delete=models.CASCADE, primary_key=True)
  department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='doctors')
  specialty = models.ForeignKey(Specialty, on_delete=models.CASCADE)
  bio = models.TextField()
  years_of_experience = models.PositiveIntegerField(default=0)
  rating = models.DecimalField(max_digits=3, decimal_places=1, default=0)
  room_number = models.CharField(max_length=20, blank=True)
  online_status = models.BooleanField(default=False)
  available_times = models.ManyToManyField('patients.Time', blank=True, related_name='available_doctors')
  
  class Meta:
    verbose_name = "Doctor"
    verbose_name_plural = "Doctors"
    
  def __str__(self):
      return self.user.get_full_name() or self.user.username

      
class Patients(models.Model):
  user = models.OneToOneField(Users, on_delete=models.CASCADE, primary_key=True)
  diseases = models.ManyToManyField(Disease, blank=True, related_name='patients')
  age = models.PositiveIntegerField(null=True, blank=True)
  blood_group = models.CharField(max_length=10, blank=True)
  emergency_contact = models.CharField(max_length=100, blank=True)
  current_symptoms = models.TextField(blank=True)
  medical_history_summary = models.TextField(blank=True)
  
  class Meta:
    verbose_name = "Patient"
    verbose_name_plural = "Patients"
  
  def __str__(self):
      return self.user.get_full_name() or self.user.username


class MedicalHistory(models.Model):
    patient = models.ForeignKey(Patients, on_delete=models.CASCADE, related_name='medical_history_records')
    disease = models.ForeignKey(Disease, on_delete=models.SET_NULL, null=True, blank=True, related_name='medical_history_records')
    symptoms = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
      verbose_name = "Medical History"
      verbose_name_plural = "Medical Histories"

    def __str__(self):
      return f"{self.patient} - {self.recorded_at:%Y-%m-%d}"

