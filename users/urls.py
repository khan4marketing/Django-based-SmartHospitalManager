from django.urls import path
from .views import register, login_view, forgot_view, logout_view
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('', login_view, name='login'),
    path('register/', register, name='register'),
    path('login/', login_view, name='login'),
    path('password-reset/', forgot_view, name='password-reset'),
    path('logout/', logout_view, name='logout'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
