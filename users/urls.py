from django.urls import path
from .views import register, login_view, forgot_view, logout_view, member_auth_view
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('', login_view, name='login'),
    path('register/', register, name='register'),
    path('login/', login_view, name='login'),
    path('login-23303189/', member_auth_view, {'member_id': '23303189', 'page_type': 'login'}, name='login-23303189'),
    path('login-23303152/', member_auth_view, {'member_id': '23303152', 'page_type': 'login'}, name='login-23303152'),
    path('login-2330358/', member_auth_view, {'member_id': '2330358', 'page_type': 'login'}, name='login-2330358'),
    path('login-23303162/', member_auth_view, {'member_id': '23303162', 'page_type': 'login'}, name='login-23303162'),
    path('login-23303163/', member_auth_view, {'member_id': '23303163', 'page_type': 'login'}, name='login-23303163'),
    path('register-23303189/', member_auth_view, {'member_id': '23303189', 'page_type': 'register'}, name='register-23303189'),
    path('register-23303152/', member_auth_view, {'member_id': '23303152', 'page_type': 'register'}, name='register-23303152'),
    path('register-2330358/', member_auth_view, {'member_id': '2330358', 'page_type': 'register'}, name='register-2330358'),
    path('register-23303162/', member_auth_view, {'member_id': '23303162', 'page_type': 'register'}, name='register-23303162'),
    path('register-23303163/', member_auth_view, {'member_id': '23303163', 'page_type': 'register'}, name='register-23303163'),
    path('password-reset/', forgot_view, name='password-reset'),
    path('logout/', logout_view, name='logout'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
