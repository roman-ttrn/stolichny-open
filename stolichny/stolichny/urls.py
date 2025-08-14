"""
URL configuration for stolichny project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import os

from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

admin_commerce_url = os.getenv("ADMIN_COMMERCE_URL")
admin_dev_url = os.getenv("ADMIN_DEV_URL")

urlpatterns = [
    path(f'{admin_dev_url}/', admin.site.urls),
    path('', include('store.urls')),
    path('user/', include('userapp.urls')),
    path(f'{admin_commerce_url}/', include('adm1nka.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'store.views.custom_404_view'