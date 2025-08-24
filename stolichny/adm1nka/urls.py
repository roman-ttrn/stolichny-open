from django.urls import path
from . import views

urlpatterns = [
    path('login-adm1n/', views.login_view, name='admin_login'),
    path('dashboard-adm1in/', views.admin_dashboard, name='admin_dashboard'),
    path('update-order-adm1n/<int:order_id>/', views.update_order_status, name='update_order_status'),
    path('product-create/', views.product_create_or_edit, name='product_create'),
    path('product_edit/<int:product_id>/', views.product_create_or_edit, name='product_edit'),
    path('product_delete/<int:product_id>/', views.product_delete, name='product_delete'),
]