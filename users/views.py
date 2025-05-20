from django.contrib.auth import get_user_model, update_session_auth_hash, login, logout
from django.contrib.auth.views import PasswordChangeView
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.db.models import Count, Q
from courses.models import Course, Attendance, Submission, Payments
from datetime import datetime, timedelta
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

from .forms import (
    CustomUserCreationForm, ProfileUpdateForm,
    TeacherCreationForm, TeacherUpdateForm, UserForm,
    StudentCreationForm, StudentUpdateForm, CustomUserChangeForm,
    CustomPasswordChangeForm
)
from .models import User

# Récupérer le modèle User personnalisé
User = get_user_model()

def send_welcome_email(request, user, password, sender_email=None):
    """
    Envoie un email de bienvenue à un nouvel utilisateur avec ses informations de connexion.

    Args:
        request: La requête HTTP
        user: L'utilisateur qui vient d'être créé
        password: Le mot de passe en clair de l'utilisateur
        sender_email: L'adresse email de l'expéditeur (si None, utilise l'email par défaut)
    """
    subject = 'Bienvenue sur la plateforme E-learning'

    # Préparer le contexte pour le template d'email
    context = {
        'user': user,
        'password': password,
        'login_url': request.build_absolute_uri(reverse_lazy('users:login')),
        'site_name': 'Plateforme E-learning',
        'admin_email': sender_email or settings.DEFAULT_FROM_EMAIL
    }

    # Rendre le contenu HTML de l'email
    html_message = render_to_string('emails/welcome_email.html', context)
    plain_message = strip_tags(html_message)

    # Utiliser l'email configuré dans les paramètres comme expéditeur
    from_email = settings.DEFAULT_FROM_EMAIL
    headers = {'Reply-To': sender_email} if sender_email else None

    try:
        # Envoyer l'email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=from_email,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
            headers=headers
        )

        # Afficher un message de confirmation dans la console
        print(f"Email envoyé à {user.email} avec succès!")
        print(f"Vérifiez le dossier 'sent_emails' pour voir le contenu de l'email.")

        return True
    except Exception as e:
        # Log l'erreur pour le débogage
        print(f"Erreur lors de l'envoi de l'email: {str(e)}")
        return False

def home(request):
    context = {}

    # Pour les utilisateurs non connectés
    if not request.user.is_authenticated:
        # Récupérer les derniers cours
        context['latest_courses'] = Course.objects.all().order_by('-created_at')[:3]
        return render(request, 'home.html', context)

    # Statistiques communes pour tous les utilisateurs connectés
    context['total_users'] = User.objects.count()
    context['total_courses'] = Course.objects.count()
    context['total_students'] = User.objects.filter(role='student').count()
    context['total_teachers'] = User.objects.filter(role='teacher').count()

    # Pour les superutilisateurs (admins)
    if request.user.is_superuser:
        # Statistiques des cours par niveau
        context['courses_beginner'] = Course.objects.filter(level='beginner').count()
        context['courses_intermediate'] = Course.objects.filter(level='intermediate').count()
        context['courses_advanced'] = Course.objects.filter(level='advanced').count()

        # Statistiques des assignments par cours
        courses = Course.objects.all()
        context['courses_labels'] = [course.title for course in courses]
        context['assignments_data'] = [course.assignments.count() for course in courses]

        # Statistiques des présences
        context['recent_attendances'] = Attendance.objects.filter(date__gte=datetime.now() - timedelta(days=7)).count()

    # Pour les enseignants
    elif request.user.is_teacher:
        # Récupérer les cours de l'enseignant
        teacher_courses = Course.objects.filter(teacher=request.user)
        context['teacher_courses_count'] = teacher_courses.count()

        # Récupérer les étudiants inscrits aux cours de l'enseignant
        student_ids = set()
        for course in teacher_courses:
            student_ids.update(course.enrolled_students.values_list('id', flat=True))
        context['teacher_students_count'] = len(student_ids)

        # Récupérer le nombre de ressources créées par l'enseignant
        context['teacher_resources_count'] = sum(course.resources.count() for course in teacher_courses)

        # Récupérer les cours récents de l'enseignant
        context['recent_courses'] = teacher_courses.order_by('-created_at')[:3]

    # Pour les étudiants
    elif request.user.is_student:
        # Récupérer les cours auxquels l'étudiant est inscrit
        enrollments = Payments.objects.filter(student=request.user)
        context['enrolled_courses_count'] = enrollments.count()

        # Récupérer le nombre de cours complétés
        context['completed_courses_count'] = enrollments.filter(completed=True).count()

        # Récupérer les inscriptions récentes
        context['enrolled_courses'] = enrollments.order_by('-enrolled_at')[:6]

        # Récupérer tous les cours pour les recommandations
        context['courses_list'] = Course.objects.all().order_by('-created_at')[:6]

        # Récupérer les soumissions de l'étudiant
        student_submissions = Submission.objects.filter(student=request.user)
        context['submissions_count'] = student_submissions.count()
        context['validated_submissions_count'] = student_submissions.filter(status='validated').count()
        context['recent_submissions'] = student_submissions.order_by('-submitted_at')[:3]

    return render(request, 'home.html', context)

class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('users:login')
    template_name = 'registration/signup.html'

    def form_valid(self, form):
        user = form.save(commit=False)
        user.role = 'student'  # Forcer le rôle étudiant
        user.save()
        messages.success(self.request, 'Votre compte a été créé avec succès !')
        return redirect(self.success_url)

def logout_view(request):
    logout(request)
    messages.success(request, 'Vous avez été déconnecté avec succès.')
    return redirect('home')

def profile(request):
    user = request.user
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil mis à jour avec succès.')
            return redirect('users:profile')
    else:
        form = ProfileUpdateForm(instance=user)
    return render(request, 'registration/profile.html', {'form': form})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def create_teacher(request):
    if request.method == 'POST':
        form = TeacherCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            messages.success(request, "L'enseignant a été créé avec succès.")

            # Envoyer un email de bienvenue si demandé
            if form.cleaned_data.get('send_welcome_email'):
                # Utiliser l'email du superuser connecté comme expéditeur
                sender_email = request.user.email
                email_sent = send_welcome_email(request, user, form.cleaned_data.get('password1'), sender_email)
                if email_sent:
                    messages.success(request, "Un email de bienvenue a été envoyé à l'enseignant. Vérifiez le dossier 'sent_emails' pour voir le contenu.")
                else:
                    messages.error(request, "L'email de bienvenue n'a pas pu être envoyé. Vérifiez la configuration email et les logs.")

            return redirect('users:teacher_list')
    else:
        form = TeacherCreationForm()

    context = {
        'form': form,
        'title': 'Ajouter un enseignant',
        'submit_text': 'Créer',
        'cancel_url': reverse_lazy('users:teacher_list'),
        'back_text': 'Annuler',
    }
    return render(request, 'users/teacher_form.html', context)

@login_required
def teacher_list(request):
    query = request.GET.get('q', '')
    teachers = User.objects.filter(role='teacher')

    if query:
        teachers = teachers.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(bio__icontains=query)
        )

    context = {
        'teachers': teachers,
        'query': query,
        'title': 'Liste des enseignants',
        'user_type': 'teacher'
    }
    return render(request, 'users/teacher_list.html', context)

def edit_teacher(request, pk):
    teacher = get_object_or_404(User, pk=pk, role='teacher')
    if request.method == 'POST':
        form = TeacherUpdateForm(request.POST, request.FILES, instance=teacher)
        if form.is_valid():
            form.save()
            return redirect('users:teacher_list')
    else:
        form = TeacherUpdateForm(instance=teacher)
    return render(request, 'users/edit_teacher.html', {'form': form, 'teacher': teacher})

def delete_teacher(request, pk):
    teacher = get_object_or_404(User, pk=pk, role='teacher')
    teacher.delete()
    messages.success(request, "L'enseignant a été supprimé avec succès.")
    return redirect('users:teacher_list')

def student_list(request):
    query = request.GET.get('q', '')
    students = User.objects.filter(role='student')

    if query:
        students = students.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(bio__icontains=query)
        )

    context = {
        'students': students,
        'query': query,
        'title': 'Liste des étudiants',
        'user_type': 'student'
    }
    return render(request, 'users/student_list.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def create_student(request):
    if request.method == 'POST':
        form = StudentCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            messages.success(request, "L'étudiant a été créé avec succès.")

            # Envoyer un email de bienvenue si demandé
            if form.cleaned_data.get('send_welcome_email'):
                # Utiliser l'email du superuser connecté comme expéditeur
                sender_email = request.user.email
                email_sent = send_welcome_email(request, user, form.cleaned_data.get('password1'), sender_email)
                if email_sent:
                    messages.success(request, "Un email de bienvenue a été envoyé à l'étudiant. Vérifiez le dossier 'sent_emails' pour voir le contenu.")
                else:
                    messages.error(request, "L'email de bienvenue n'a pas pu être envoyé. Vérifiez la configuration email et les logs.")

            return redirect('users:student_list')
    else:
        form = StudentCreationForm()

    context = {
        'form': form,
        'title': 'Ajouter un étudiant',
        'submit_text': 'Créer',
        'cancel_url': reverse_lazy('users:student_list'),
        'back_text': 'Annuler',
    }
    return render(request, 'users/student_form.html', context)

def edit_student(request, id):
    student = get_object_or_404(User, id=id, role='student')
    if request.method == 'POST':
        form = StudentUpdateForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, "Les informations de l'étudiant ont été mises à jour avec succès.")
            return redirect('users:student_list')
    else:
        form = StudentUpdateForm(instance=student)

    context = {
        'form': form,
        'title': 'Modifier étudiant',
        'submit_text': 'Mettre à jour',
        'back_url': reverse_lazy('users:student_list'),
        'back_text': 'Annuler',
        'student': student
    }
    return render(request, 'users/student_form.html', context)

def delete_student(request, id):
    student = get_object_or_404(User, id=id, role='student')
    if request.method == 'POST':
        student.delete()
        messages.success(request, "L'étudiant a été supprimé avec succès.")
        return redirect('users:student_list')
    return render(request, 'users/student_confirm_delete.html', {'student': student})

class CustomPasswordChangeView(PasswordChangeView):
    """Vue personnalisée pour le changement de mot de passe.
    S'assure que l'utilisateur est connecté et redirige vers la page de profil après la modification."""
    form_class = CustomPasswordChangeForm
    template_name = 'users/password_change.html'
    success_url = reverse_lazy('users:profile')

    def get_success_url(self):
        messages.success(self.request, 'Votre mot de passe a été modifié avec succès !')
        return super().get_success_url()

    def form_valid(self, form):
        """Si le formulaire est valide, enregistrer le formulaire et rediriger vers l'URL de succès."""
        # Sauvegarder le formulaire (ce qui met à jour le mot de passe)
        form.save()
        # Mettre à jour la session pour maintenir l'utilisateur connecté
        update_session_auth_hash(self.request, form.user)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        """Ajouter des variables supplémentaires au contexte du template."""
        context = super().get_context_data(**kwargs)
        context['title'] = 'Changer le mot de passe'
        return context

@login_required
@user_passes_test(lambda u: u.is_superuser)
def teacher_stats(request):
    """Vue pour afficher les statistiques des enseignants"""
    teachers = User.objects.filter(role='teacher')

    # Statistiques par matière enseignée
    subjects = {}
    for teacher in teachers:
        for course in teacher.courses.all():
            subjects[course.subject] = subjects.get(course.subject, 0) + 1


    # Statistiques de présence
    attendance_stats = {
        'total': Attendance.objects.filter(teacher__in=teachers).count(),
        'recent': Attendance.objects.filter(
            teacher__in=teachers,
            date__gte=datetime.now() - timedelta(days=30)
        ).count()
    }

    context = {
        'teachers': teachers,
        'subjects': sorted(subjects.items()),
        'attendance_stats': attendance_stats,
    }
    return render(request, 'users/teacher_stats.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def attendance_list(request):
    """Vue pour afficher la liste des présences"""
    attendances = Attendance.objects.all().order_by('-date')
    context = {
        'attendances': attendances
    }
    return render(request, 'users/attendance_list.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def reports(request):
    """Vue pour afficher les rapports"""
    # Statistiques générales
    total_users = User.objects.count()
    total_students = User.objects.filter(role='student').count()
    total_teachers = User.objects.filter(role='teacher').count()

    # Statistiques des cours
    course_stats = Course.objects.annotate(
        student_count=Count('students'),
        assignment_count=Count('assignments')
    ).values('title', 'student_count', 'assignment_count')

    # Statistiques des présences
    attendance_stats = Attendance.objects.filter(
        date__gte=datetime.now() - timedelta(days=30)
    ).values('course__title').annotate(
        total_attendance=Count('id')
    )

    context = {
        'total_users': total_users,
        'total_students': total_students,
        'total_teachers': total_teachers,
        'course_stats': course_stats,
        'attendance_stats': attendance_stats,
    }
    return render(request, 'users/reports.html', context)
