from django.urls import path
from . import views

urlpatterns = [
    path('login/email/', views.login_email, name='login_email'),
    path('login/email/verify/<str:email>/', views.login_email_verify, name='login_email_verify'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('signup/email/', views.signup_email, name='signup_email'),
    path('signup/email/verification/', views.signup_email_verification, name='signup_email_verification'),
    path('logout_user/', views.logout_user, name='logout_user'),
    path('resend_code/', views.resend_code, name='resend_code'),
]