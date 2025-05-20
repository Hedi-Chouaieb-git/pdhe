from django import forms
from .models import Course, Resource, Assignment, Submission

class CourseForm(forms.ModelForm):
    access_key = forms.CharField(
        required=False,
        max_length=255,
        widget=forms.PasswordInput(attrs={'placeholder': 'Clé d\'accès (optionnelle)'}),
        label='Clé d\'accès'
    )

    class Meta:
        model = Course
        fields = ['title', 'description', 'level', 'access_key']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Entrez la description du cours...'}),
            'title': forms.TextInput(attrs={'placeholder': 'Entrez le nom du cours...'}),
            'level': forms.Select(),
        }


class ResourceForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = ['title', 'description', 'file']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            valid_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png']
            if not any(file.name.lower().endswith(ext) for ext in valid_extensions):
                raise forms.ValidationError("Format de fichier non supporté.")
        return file


class AssignmentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['due_date'].label = "Date limite"

    class Meta:
        model = Assignment
        fields = ['title', 'description', 'assignment_type', 'due_date', 'file']  # Ajout du champ 'file'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            valid_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png']
            if not any(file.name.lower().endswith(ext) for ext in valid_extensions):
                raise forms.ValidationError("Format de fichier non supporté.")
        return file
    
class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['file']


class CourseEnrollForm(forms.Form):
    access_key = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={'placeholder': 'Entrez la clé d\'accès du cours...'}),
        label='Clé d\'accès'
    )
