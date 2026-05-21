DISEASE_SPECIALTY_MAP = {
    'Heart Disease': ['Cardiology', 'General Health'],
    'Skin Disease': ['Dermatology', 'General Health'],
    'Bone and Joint Problems': ['Orthopedics', 'Rheumatology'],
    'Digestive Disease': ['Gastroenterology', 'General Health'],
    'Brain and Nerve Disease': ['Neurology', 'Psychiatry'],
    'Eye Disease': ['Ophthalmology', 'General Health'],
    'Child Health Issues': ['Pediatrics', 'General Health'],
    'Mental Health Disorder': ['Psychiatry', 'General Health'],
}

DEPARTMENT_SPECIALTY_MAP = {
    'Cardiology': ['Cardiology'],
    'General Medicine': ['General Health'],
    'Dermatology': ['Dermatology'],
    'Orthopedics': ['Orthopedics'],
    'Rheumatology': ['Rheumatology'],
    'Gastroenterology': ['Gastroenterology'],
    'Neurology': ['Neurology'],
    'Psychiatry': ['Psychiatry'],
    'Ophthalmology': ['Ophthalmology'],
    'Pediatrics': ['Pediatrics'],
}


def ensure_disease_specialty_reference_data(Specialty, Disease):
    """Create the reference departments, specialties, and diseases."""
    Department = Specialty._meta.get_field('department').remote_field.model

    departments = {}
    for department_name in DEPARTMENT_SPECIALTY_MAP:
        department, _ = Department.objects.get_or_create(
            name=department_name,
            defaults={'description': f'{department_name} department.'},
        )
        departments[department_name] = department

    all_specialties = set()
    for related_specialties in DISEASE_SPECIALTY_MAP.values():
        all_specialties.update(related_specialties)

    for specialty_name in all_specialties:
        specialty, _ = Specialty.objects.get_or_create(
            name=specialty_name,
            defaults={'description': f'{specialty_name} specialist care.'},
        )
        for department_name, specialty_names in DEPARTMENT_SPECIALTY_MAP.items():
            if specialty_name in specialty_names:
                specialty.department = departments[department_name]
                specialty.save(update_fields=['department'])
                break

    for disease_name, related_specialties in DISEASE_SPECIALTY_MAP.items():
        disease, _ = Disease.objects.get_or_create(
            name=disease_name,
            defaults={'description': f'History of {disease_name.lower()}.'},
        )
        disease_specialties = Specialty.objects.filter(name__in=related_specialties)
        disease.specialties.set(disease_specialties)

        disease_department = None
        for specialty in disease_specialties:
            if specialty.department:
                disease_department = specialty.department
                break

        if disease_department and disease.suggested_department_id != disease_department.id:
            disease.suggested_department = disease_department
            disease.save(update_fields=['suggested_department'])

    return Disease.objects.all().order_by('name')