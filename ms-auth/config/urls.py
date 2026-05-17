"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.contrib import admin
from django.urls import path
from apps.core.views import login, refresh_token, get_me, forgot_password, reset_password, logout, admin_only, docente_only, alumno_only, usuarios, usuario_detail, usuario_reset_password

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Auth endpoints
    path('auth/login', login, name='login'),
    path('auth/refresh-token', refresh_token, name='refresh_token'),
    path('auth/me', get_me, name='get_me'),
    path('auth/forgot-password', forgot_password, name='forgot_password'),
    path('auth/reset-password', reset_password, name='reset_password'),
    path('auth/logout', logout, name='logout'),
    path('auth/admin-only', admin_only, name='admin_only'),
    path('auth/docente-only', docente_only, name='docente_only'),
    path('auth/alumno-only', alumno_only, name='alumno_only'),

    # Admin users
    path('usuarios', usuarios, name='usuarios'),
    path('usuarios/<int:user_id>', usuario_detail, name='usuario_detail'),
    path('usuarios/<int:user_id>/reset-password', usuario_reset_password, name='usuario_reset_password'),
]
