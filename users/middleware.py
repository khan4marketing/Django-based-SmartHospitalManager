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

    def __call__(self, request):
        path = request.path_info.lstrip('/')

        if not request.user.is_authenticated:
            if path.startswith(self.protected_prefixes):
                return redirect('login')

        return self.get_response(request)
