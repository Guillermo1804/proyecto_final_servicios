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
<<<<<<< HEAD
from config.health_views import health
from apps.core.views import login, refresh_token, get_me, forgot_password, reset_password, logout, admin_only, docente_only, alumno_only, usuarios, usuario_detail, usuario_reset_password
=======
from apps.core.views import login
>>>>>>> parent of 04b6ece (cambios de ms auth)

urlpatterns = [
    path('health/', health, name='health'),
    path('admin/', admin.site.urls),
    path('auth/login', login, name='login'),
]
