from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django import forms
from django.contrib.auth.hashers import make_password

from .models import Users, Address, Doctors, Patients


try:
	admin.site.unregister(Group)
except admin.sites.NotRegistered:
	pass


class UsersAdminForm(forms.ModelForm):
	security_key_answer = forms.CharField(
		required=False,
		widget=forms.PasswordInput(render_value=False),
		help_text='Enter a new answer only when you want to change the security key answer.',
		label='Security Key Answer',
	)

	class Meta:
		model = Users
		fields = '__all__'

	def save(self, commit=True):
		instance = super().save(commit=False)
		new_answer = (self.cleaned_data.get('security_key_answer') or '').strip().lower()
		if new_answer:
			instance.recovery_answer = make_password(new_answer)
		if commit:
			instance.save()
		return instance


@admin.register(Users)
class UsersAdmin(UserAdmin):
	form = UsersAdminForm
	list_display = (
		'username',
		'email',
		'first_name',
		'last_name',
		'security_key_question',
		'has_security_key',
		'is_doctor',
		'is_staff',
		'is_active',
	)
	list_filter = ('is_doctor', 'is_staff', 'is_superuser', 'is_active')
	search_fields = ('username', 'email', 'first_name', 'last_name', 'recovery_question')
	ordering = ('username',)
	fieldsets = UserAdmin.fieldsets + (
		(
			'Profile Details',
			{'fields': ('gender', 'birthday', 'profile_avatar', 'id_address', 'is_doctor', 'recovery_question', 'security_key_answer')},
		),
	)

	def security_key_question(self, obj):
		return obj.get_recovery_question_display() if obj.recovery_question else '-'

	security_key_question.short_description = 'Security Key'

	def has_security_key(self, obj):
		return bool(obj.recovery_answer)

	has_security_key.short_description = 'Key Saved'
	has_security_key.boolean = True


@admin.register(Doctors)
class DoctorsAdmin(admin.ModelAdmin):
	list_display = ('full_name', 'username', 'email', 'specialty', 'security_key')
	search_fields = (
		'user__username',
		'user__first_name',
		'user__last_name',
		'user__email',
		'specialty__name',
		'user__recovery_question',
	)
	list_select_related = ('user', 'specialty')

	def full_name(self, obj):
		return obj.user.get_full_name() or obj.user.username

	full_name.short_description = 'Name'

	def username(self, obj):
		return obj.user.username

	def email(self, obj):
		return obj.user.email

	def security_key(self, obj):
		return obj.user.get_recovery_question_display() if obj.user.recovery_question else '-'

	security_key.short_description = 'Security Key'


@admin.register(Patients)
class PatientsAdmin(admin.ModelAdmin):
	list_display = ('full_name', 'username', 'email', 'previous_disease', 'security_key')
	search_fields = (
		'user__username',
		'user__first_name',
		'user__last_name',
		'user__email',
		'previous_disease',
		'user__recovery_question',
	)
	list_select_related = ('user',)

	def full_name(self, obj):
		return obj.user.get_full_name() or obj.user.username

	full_name.short_description = 'Name'

	def username(self, obj):
		return obj.user.username

	def email(self, obj):
		return obj.user.email

	def security_key(self, obj):
		return obj.user.get_recovery_question_display() if obj.user.recovery_question else '-'

	security_key.short_description = 'Security Key'


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
	list_display = ('name', 'profession', 'address_line', 'region', 'city', 'code_postal')
	search_fields = (
		'address_line',
		'region',
		'city',
		'code_postal',
		'users__username',
		'users__first_name',
		'users__last_name',
	)

	def name(self, obj):
		users = obj.users_set.all()
		full_names = [user.get_full_name() or user.username for user in users]
		return ", ".join(full_names) if full_names else "-"

	name.short_description = 'Name'

	def profession(self, obj):
		users = obj.users_set.all()
		roles = ['Doctor' if user.is_doctor else 'Patient' for user in users]
		return ", ".join(roles) if roles else "-"

	profession.short_description = 'Profession'