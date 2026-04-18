from django.shortcuts import redirect


class LoginRequiredPathMiddleware:
    """Block direct URL access to protected pages for anonymous users."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.protected_prefixes = (
            'doctor_dashboard/',
            'patient_dashboard/',
            'doctor/profile/',
            'patient/profile/',
            'profile/',
        )
        self.doctor_only_prefixes = (
            'doctor_dashboard/',
            'doctor/profile/',
        )
        self.patient_only_prefixes = (
            'patient_dashboard/',
            'patient/profile/',
        )

    def __call__(self, request):
        path = request.path_info.lstrip('/')

        if not request.user.is_authenticated:
            if path.startswith(self.protected_prefixes):
                return redirect('login')

        if request.user.is_authenticated:
            if path.startswith(self.doctor_only_prefixes) and not request.user.is_doctor:
                return redirect('patient_dashboard')

            if path.startswith(self.patient_only_prefixes) and request.user.is_doctor:
                return redirect('doctor_dashboard')

        return self.get_response(request)
