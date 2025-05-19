# accounts/urls.py
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('password_reset/', auth_views.PasswordResetView.as_view(
        subject_template_name='password_reset_subject.txt',
        email_template_name='password_reset_email.html',
        success_url='/accounts/password_reset/done/'
    ), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='password_reset_confirm.html',
        success_url='/accounts/reset/done/'
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='password_reset_complete.html'
    ), name='password_reset_complete'),
    path('google_login/', views.google_login, name='google_login'),
    path('phone-login/', views.phone_login, name='phone_login'),
    path('auth-google/', views.AuthGoogle.as_view(), name='auth_google'),
    path('profile/', views.profile_view, name='profile'),
    path('auth-receiver/', views.auth_receiver, name='auth_receiver'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('contact/', views.contact_view, name='contact'),
    path('verify/<uuid:token>/', views.verify_email_view, name='verify_email'),
]