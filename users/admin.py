from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm
from .models import User
from courses.models import Course, Resource, Assignment, Submission

# Utiliser la configuration personnalisée du site d'administration
from .admin_site import *

# Enregistrer les autres modèles
admin.site.register(Course)
admin.site.register(Resource)
admin.site.register(Assignment)
admin.site.register(Submission)
