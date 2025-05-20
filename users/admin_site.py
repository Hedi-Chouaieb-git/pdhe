from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm
from django.utils.translation import gettext_lazy as _
from .models import User

class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Supprimer le champ de mot de passe du formulaire
        if 'password' in self.fields:
            del self.fields['password']
        # Supprimer le lien vers le formulaire de changement de mot de passe
        self.fields.pop('password', None)
        self.fields.pop('user_permissions', None)
        self.fields.pop('groups', None)

class UserAdmin(BaseUserAdmin):
    form = CustomUserChangeForm
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'role')
    
    # Modifier les champs affichés dans le formulaire d'édition
    fieldsets = (
        (None, {'fields': ('email',)}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'profile_picture', 'bio', 'cv', 'publications')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'role'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    # Champs pour la création d'utilisateur
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'role'),
        }),
    )
    
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    
    # Supprimer les actions de changement de mot de passe
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Ne pas permettre de modifier son propre compte via l'admin
        if not request.user.is_superuser:
            qs = qs.exclude(pk=request.user.pk)
        return qs
    
    # Désactiver la modification du mot de passe dans l'admin
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'password' in form.base_fields:
            del form.base_fields['password']
        return form
    
    # Supprimer le lien de changement de mot de passe
    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_save_and_continue'] = False
        extra_context['show_save'] = False
        return super().change_view(
            request, object_id, form_url, extra_context=extra_context,
        )

# Désenregistrer le modèle User par défaut s'il est déjà enregistré
if admin.site.is_registered(User):
    admin.site.unregister(User)

# Enregistrer notre modèle User personnalisé
admin.site.register(User, UserAdmin)
