from django.conf import settings
from django.core.mail import send_mail as django_send_mail


def send_email(*args, **kwargs):
    """Send email while preserving the existing password-reset call signature.

    Supports both:
    - send_email(email, token)
    - send_email(subject, message, recipient_list, from_email=None, fail_silently=True)
    """
    fail_silently = kwargs.pop('fail_silently', True)
    from_email = kwargs.pop('from_email', None)

    if len(args) == 2 and not kwargs:
        email, token = args
        subject = 'change password link'
        message = f'http://127.0.0.1:8000/reset/{token}/'
        recipient_list = [email]
    elif len(args) >= 3:
        subject, message, recipient_list = args[:3]
        if len(args) >= 4:
            from_email = args[3]
        if len(args) >= 5:
            fail_silently = args[4]
    else:
        raise TypeError('send_email expects either (email, token) or (subject, message, recipient_list, ...)')

    if from_email is None:
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@example.com')

    try:
        django_send_mail(subject, message, from_email, recipient_list, fail_silently=fail_silently)
        return True
    except Exception:
        try:
            print('send_email fallback:', subject, '->', recipient_list)
        except Exception:
            pass
        return False
