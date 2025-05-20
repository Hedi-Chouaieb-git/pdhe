"""
URL configuration for Elearn project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
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
from os import stat
from django.views.generic import RedirectView
from django.contrib import admin
from django.urls import path, include
from Elearn import settings
from users.views import home, CustomPasswordChangeView  
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),  
    path('users/', include('users.urls')),
    path('courses/', include('courses.urls')),
    path('about/', TemplateView.as_view(template_name='about.html'), name='about'),
    path('contact/', TemplateView.as_view(template_name='contact.html'), name='contact'),
    
    # Redirections pour le changement de mot de passe
    path('accounts/password/change/', RedirectView.as_view(url='/users/password/change/', permanent=True)),
    path('accounts/password_change/', RedirectView.as_view(url='/users/password/change/', permanent=True)),
    path('users/password_change/', RedirectView.as_view(url='/users/password/change/', permanent=True)),
    
    # Désactiver les autres URLs d'authentification par défaut
    # path('accounts/', include('django.contrib.auth.urls')),
]
if settings.DEBUG:
   urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

