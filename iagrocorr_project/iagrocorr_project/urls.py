"""
URL configuration for iagrocorr_project project.

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
from django.contrib import admin
from django.urls import path
from accounts.views import login_view, register_view, dashboard_view, logout_view, profile_view, demo_view, global_twins_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', login_view, name='login'),  #página en /login/
    path('register/', register_view, name='register'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('logout/', logout_view, name='logout'),       # <-- Nueva ruta
    path('profile/', profile_view, name='profile'),
    path('global-twins/', global_twins_view, name='global-twins'),
    #path('', login_view, name='home'), #pagina raiz
    path('', demo_view, name='demo')
]
