from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def doctor_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')

        if not request.user.is_doctor:
            messages.error(request, 'Access denied. Doctor account required.')
            return redirect('patient_dashboard')

        return view_func(request, *args, **kwargs)

    return _wrapped_view


def patient_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')

        if request.user.is_doctor:
            messages.error(request, 'Access denied. Patient account required.')
            return redirect('doctor_dashboard')

        return view_func(request, *args, **kwargs)

    return _wrapped_view
