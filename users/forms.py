from django import forms
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm, AuthenticationForm
from .models import User


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'bio', 'profile_picture']

class UserBaseCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Mot de passe', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirmer le mot de passe', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email']

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            self.add_error('password2', "Les mots de passe ne correspondent pas.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

class CustomUserCreationForm(UserBaseCreationForm):
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'student'
        if commit:
            user.save()
        return user

class TeacherCreationForm(UserBaseCreationForm):
    send_welcome_email = forms.BooleanField(
        label="Envoyer un email de bienvenue avec les informations de connexion",
        required=False,
        initial=True
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'profile_picture', 'bio', 'cv', 'publications']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'teacher'
        if commit:
            user.save()
        return user

class StudentCreationForm(UserBaseCreationForm):
    send_welcome_email = forms.BooleanField(
        label="Envoyer un email de bienvenue avec les informations de connexion",
        required=False,
        initial=True
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'profile_picture', 'bio']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'student'
        if commit:
            user.save()
        return user

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'bio', 'profile_picture', 'cv', 'publications']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'publications': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label="Ancien mot de passe",
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 'class': 'form-control'}),
    )
    new_password1 = forms.CharField(
        label="Nouveau mot de passe",
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'form-control'}),
        strip=False,
    )
    new_password2 = forms.CharField(
        label="Confirmation du nouveau mot de passe",
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'form-control'}),
    )

class TeacherUpdateForm(forms.ModelForm):
    password = forms.CharField(
        label="Nouveau mot de passe",
        required=False,
        widget=forms.PasswordInput(render_value=True)
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'bio', 'profile_picture', 'cv', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user


class StudentUpdateForm(forms.ModelForm):
    password = forms.CharField(
        label="Nouveau mot de passe",
        required=False,
        widget=forms.PasswordInput(render_value=True)
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'bio', 'profile_picture', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user


class CustomUserChangeForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'profile_picture', 'bio']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personnalisation des champs si nécessaire
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
        self.fields['first_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['last_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['bio'].widget.attrs.update({'class': 'form-control', 'rows': 4})

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Cet email est déjà utilisé par un autre compte.')
        return email

class CustomAuthenticationForm(AuthenticationForm):
    """
    Formulaire d'authentification personnalisé qui accepte l'email ou le nom d'utilisateur
    """
    username = forms.CharField(
        label="Email ou nom d'utilisateur",
        widget=forms.TextInput(attrs={
            'autofocus': True,
            'class': 'form-control',
            'placeholder': 'Entrez votre email ou nom d\'utilisateur'
        })
    )
    password = forms.CharField(
        label="Mot de passe",
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Entrez votre mot de passe'
        })
    )

    error_messages = {
        'invalid_login': "Identifiants incorrects. Veuillez vérifier votre email/nom d'utilisateur et votre mot de passe.",
        'inactive': "Ce compte est inactif.",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].help_text = "Vous pouvez utiliser votre adresse email ou votre nom d'utilisateur."