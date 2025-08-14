from django.urls import path
from . import views

urlpatterns = [
    path('login-adm1n/', views.login_view, name='admin_login'),
    path('dashboard-adm1in/', views.admin_dashboard, name='admin_dashboard'),
    path('update-order-adm1n/<int:order_id>/', views.update_order_status, name='update_order_status'),
]

