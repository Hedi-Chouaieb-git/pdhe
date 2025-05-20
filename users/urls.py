from django.urls import path
from . import views, forms
from django.contrib.auth import views as auth_views
from .views import CustomPasswordChangeView

app_name = 'users'

urlpatterns = [
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html', form_class=forms.CustomAuthenticationForm), name='login'),
    path('profile/', views.profile, name='profile'),
    path('logout/', views.logout_view, name='logout'),
    path('create-teacher/', views.create_teacher, name='create_teacher'),
    path('teachers/edit/<int:pk>/', views.edit_teacher, name='edit_teacher'),
    path('teachers/create/', views.create_teacher, name='create_teacher'),
    path('teachers/', views.teacher_list, name='teacher_list'),
    path('teachers/delete/<int:pk>/', views.delete_teacher, name='delete_teacher'),
    path('etudiants/', views.student_list, name='student_list'),
    path('etudiants/nouveau/', views.create_student, name='create_student'),
    path('etudiants/editer/<int:id>/', views.edit_student, name='edit_student'),
    path('etudiants/supprimer/<int:id>/', views.delete_student, name='delete_student'),

    # URLs pour les statistiques et rapports
    path('teachers/stats/', views.teacher_stats, name='teacher_stats'),
    path('attendance/', views.attendance_list, name='attendance_list'),
    path('reports/', views.reports, name='reports'),

    # URLs pour le changement de mot de passe
    path('password/change/', CustomPasswordChangeView.as_view(), name='password_change'),
    path('password/change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='registration/password_change_done.html'),
        name='password_change_done'),

    # URLs pour la réinitialisation de mot de passe
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset_form.html',
        email_template_name='registration/password_reset_email.html',
        subject_template_name='registration/password_reset_subject.txt'
    ), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'
    ), name='password_reset_complete'),
]
