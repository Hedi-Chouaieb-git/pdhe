from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from .models import Course, Resource, Assignment, Submission
from .forms import CourseForm, ResourceForm, AssignmentForm, SubmissionForm, CourseEnrollForm

class CourseListView(ListView):
    model = Course
    template_name = 'courses/course_list.html'
    context_object_name = 'courses'
    paginate_by = 9  # Nombre de cours par page

    def get_queryset(self):
        queryset = Course.objects.all()
        user = self.request.user

        # Filtrage par niveau si spécifié dans les paramètres GET
        level = self.request.GET.get('level')
        if level:
            queryset = queryset.filter(level=level)

        # Filtrage par recherche si spécifié dans les paramètres GET
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query)
            )

        if user.is_authenticated:
            if hasattr(user, 'is_teacher') and user.is_teacher:
                # Les enseignants voient leurs propres cours
                return queryset.filter(teacher=user)
            elif user.is_superuser or user.is_staff:
                # Les admins voient tous les cours
                return queryset
            else:
                # Les étudiants voient tous les cours disponibles
                return queryset
        else:
            # Si l'utilisateur n'est pas connecté, montrer tous les cours
            return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Récupérer les choix de niveau depuis le modèle Course
        context['level_choices'] = Course.LEVEL_CHOICES
        return context


class CourseDetailView(DetailView):
    model = Course
    template_name = 'courses/course_detail.html'
    context_object_name = 'course'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = context['course']
        user = self.request.user

        # Initialiser les valeurs par défaut pour éviter les erreurs
        context['debug_is_superuser'] = False
        context['debug_is_teacher'] = False
        context['is_enrolled'] = False
        context['can_view_students'] = False

        if user.is_authenticated:
            context['debug_is_superuser'] = user.is_superuser
            context['debug_is_teacher'] = hasattr(course, 'teacher') and user == course.teacher
            context['is_enrolled'] = course.enrolled_students.filter(id=user.id).exists()

            # Ajouter la liste des étudiants uniquement pour l'administrateur ou l'enseignant du cours
            if user.is_superuser or (hasattr(course, 'teacher') and user == course.teacher):
                context['enrolled_students'] = course.enrolled_students.all()
                context['can_view_students'] = True

            # Formulaire d'inscription pour les étudiants non inscrits
            if hasattr(user, 'is_student') and user.is_student and not context['is_enrolled']:
                context['enroll_form'] = CourseEnrollForm()

        # Récupérer les ressources du cours
        context['resources'] = course.resources.all()

        # Récupérer les devoirs et marquer ceux qui ont été soumis
        assignments = course.assignments.all()
        for assignment in assignments:
            assignment.is_submitted = False
            if user.is_authenticated and hasattr(user, 'is_student') and user.is_student:
                assignment.is_submitted = assignment.submissions.filter(student=user).exists()
        context['assignments'] = assignments

        return context

class CourseCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Course
    form_class = CourseForm
    template_name = 'courses/course_form.html'
    success_url = reverse_lazy('courses:course_list')

    def test_func(self):
        # Allow both teachers and superusers to create courses
        is_teacher = hasattr(self.request.user, 'is_teacher') and self.request.user.is_teacher
        return is_teacher or self.request.user.is_superuser

    def form_valid(self, form):
        # If the user is a superuser and not a teacher, we need to handle this case
        if self.request.user.is_superuser and not (hasattr(self.request.user, 'is_teacher') and self.request.user.is_teacher):
            # For superusers, we need to set a teacher for the course
            # We'll use the first teacher in the system or keep it as the superuser if no teachers exist
            from django.contrib.auth import get_user_model
            User = get_user_model()
            teachers = User.objects.filter(is_teacher=True)
            if teachers.exists():
                form.instance.teacher = teachers.first()
            else:
                form.instance.teacher = self.request.user
        else:
            # For regular teachers, set the teacher field to the current logged-in user
            form.instance.teacher = self.request.user

        messages.success(self.request, 'Cours créé avec succès!')
        return super().form_valid(form)



class CourseUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Course
    form_class = CourseForm
    template_name = 'courses/course_form.html'
    success_url = reverse_lazy('courses:course_list')

    def test_func(self):
        is_teacher = hasattr(self.request.user, 'is_teacher') and self.request.user.is_teacher
        return (is_teacher and self.get_object().teacher == self.request.user) or self.request.user.is_superuser

    def form_valid(self, form):
        messages.success(self.request, 'Cours mis à jour avec succès!')
        return super().form_valid(form)

class CourseDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Course
    success_url = reverse_lazy('courses:course_list')
    template_name = 'courses/course_confirm_delete.html'

    def test_func(self):
        is_teacher = hasattr(self.request.user, 'is_teacher') and self.request.user.is_teacher
        return (is_teacher and self.get_object().teacher == self.request.user) or self.request.user.is_superuser

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Cours supprimé avec succès!')
        return super().delete(request, *args, **kwargs)

@login_required
def enroll_course(request, pk):
    course = get_object_or_404(Course, pk=pk)

    if request.method == 'POST':
        form = CourseEnrollForm(request.POST)

        if form.is_valid():
            access_key = form.cleaned_data['access_key']

            # Vérification de la clé d'accès
            if course.access_key == access_key:
                if request.user not in course.enrolled_students.all():
                    course.enrolled_students.add(request.user)
                    messages.success(request, 'Vous êtes maintenant inscrit à ce cours!')
                else:
                    messages.info(request, 'Vous êtes déjà inscrit à ce cours.')
            else:
                messages.error(request, 'Clé d\'accès incorrecte!')
        else:
            messages.error(request, 'Veuillez saisir la clé d\'accès.')

        return redirect('courses:course_detail', pk=course.pk)

    else:
        form = CourseEnrollForm()

    return render(request, 'courses/course_detail.html', {'form': form, 'course': course})

def unroll_course(request, pk):
    course = get_object_or_404(Course, pk=pk)

    if request.user.is_authenticated and request.user.is_student:
        # Désinscrire l'étudiant
        course.enrolled_students.remove(request.user)
        return redirect('courses:course_detail', pk=course.pk)

    return redirect('courses:course_list')

class ResourceCreateView(LoginRequiredMixin, CreateView):
    model = Resource
    form_class = ResourceForm
    template_name = 'courses/resource_form.html'

    def form_valid(self, form):
        # Assure-toi de récupérer le cours et de l'affecter à la ressource
        course = get_object_or_404(Course, pk=self.kwargs['course_pk'])
        form.instance.course = course
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        # Passe l'objet `course` au template
        context = super().get_context_data(**kwargs)
        course_pk = self.kwargs.get('course_pk')
        if course_pk:
            context['course'] = get_object_or_404(Course, pk=course_pk)
        return context

    def get_success_url(self):
        # Redirige vers le détail du cours après avoir ajouté la ressource
        return reverse_lazy('courses:course_detail', kwargs={'pk': self.kwargs['course_pk']})

class AssignmentCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Assignment
    form_class = AssignmentForm
    template_name = 'courses/assignment_form.html'

    def test_func(self):
        course_pk = self.kwargs.get('course_pk')
        if not course_pk:
            return False
        course = get_object_or_404(Course, pk=course_pk)
        return self.request.user.is_teacher and course.teacher == self.request.user

    def form_valid(self, form):
        course_pk = self.kwargs.get('course_pk')
        if course_pk:
            form.instance.course = get_object_or_404(Course, pk=course_pk)
            messages.success(self.request, 'TP/TD créé avec succès!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course_pk = self.kwargs.get('course_pk')
        if course_pk:
            context['course'] = get_object_or_404(Course, pk=course_pk)
        return context

    def get_success_url(self):
        course_pk = self.kwargs.get('course_pk')
        if course_pk:
            return reverse_lazy('courses:course_detail', kwargs={'pk': course_pk})
        return reverse_lazy('courses:course_list')

class SubmissionCreateView(LoginRequiredMixin, CreateView):
    model = Submission
    form_class = SubmissionForm
    template_name = 'courses/submission_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        assignment_pk = self.kwargs.get('assignment_pk')
        if assignment_pk:
            assignment = get_object_or_404(Assignment, pk=assignment_pk)
            context['assignment'] = assignment
            context['course'] = assignment.course
        return context

    def form_valid(self, form):
        assignment_pk = self.kwargs.get('assignment_pk')
        if not assignment_pk:
            messages.error(self.request, "Aucun TP/TD spécifié.")
            return redirect('courses:course_list')

        assignment = get_object_or_404(Assignment, pk=assignment_pk)
        course = assignment.course

        # Vérifie que l'utilisateur est inscrit
        if self.request.user not in course.enrolled_students.all():
            messages.error(self.request, "Vous devez être inscrit pour soumettre ce travail.")
            return redirect('courses:course_detail', pk=course.pk)

        form.instance.assignment = assignment
        form.instance.student = self.request.user
        messages.success(self.request, 'Travail soumis avec succès!')
        return super().form_valid(form)

    def get_success_url(self):
        assignment_pk = self.kwargs.get('assignment_pk')
        if not assignment_pk:
            return reverse_lazy('courses:course_list')

        assignment = get_object_or_404(Assignment, pk=assignment_pk)
        return reverse_lazy('courses:course_detail', kwargs={'pk': assignment.course.pk})

class ResourceUpdateView(LoginRequiredMixin, UpdateView):
    model = Resource
    form_class = ResourceForm
    template_name = 'courses/resource_form.html'

    def get_success_url(self):
        return reverse_lazy('courses:course_detail', kwargs={'pk': self.object.course.pk})

    def dispatch(self, request, *args, **kwargs):
        resource = self.get_object()
        if request.user != resource.course.teacher:
            messages.error(request, "Vous n'avez pas l'autorisation.")
            return redirect('courses:course_detail', pk=resource.course.pk)
        return super().dispatch(request, *args, **kwargs)

@login_required
def student_courses(request):
    courses = Course.objects.filter(enrolled_students=request.user)
    return render(request, 'courses/student_courses.html', {'courses': courses})

@login_required
def delete_resource(request, course_pk, pk):
    resource = get_object_or_404(Resource, pk=pk, course__pk=course_pk)
    if request.user == resource.course.teacher:
        resource.delete()
        messages.success(request, "Ressource supprimée avec succès.")
    else:
        messages.error(request, "Vous n'avez pas la permission de supprimer cette ressource.")
    return redirect('courses:course_detail', pk=course_pk)


@login_required
def delete_assignment(request, course_pk, pk):
    assignment = get_object_or_404(Assignment, pk=pk, course__pk=course_pk)
    if request.user == assignment.course.teacher:
        assignment.delete()
        messages.success(request, "TP/TD supprimé avec succès.")
    else:
        messages.error(request, "Vous n'avez pas la permission de supprimer ce TP/TD.")
    return redirect('courses:course_detail', pk=course_pk)


@login_required
def course_students_list(request, course_pk):
    course = get_object_or_404(Course, pk=course_pk)

    # Vérifier si l'utilisateur est l'enseignant du cours ou un administrateur
    if request.user != course.teacher and not request.user.is_superuser:
        messages.error(request, "Vous n'avez pas la permission d'accéder à cette page.")
        return redirect('courses:course_list')

    students = course.enrolled_students.all()
    return render(request, 'courses/course_students_list.html', {
        'course': course,
        'students': students
    })


@login_required
def submission_list(request, course_pk, assignment_pk):
    course = get_object_or_404(Course, pk=course_pk)
    assignment = get_object_or_404(Assignment, pk=assignment_pk, course=course)

    # Vérification des rôles
    is_teacher = hasattr(request.user, 'is_teacher') and request.user.is_teacher
    is_student = hasattr(request.user, 'is_student') and request.user.is_student

    if not is_teacher and not is_student and not request.user.is_superuser:
        messages.error(request, "Vous n'avez pas les permissions nécessaires pour accéder à cette page.")
        return redirect('courses:course_list')

    # Si l'utilisateur est un étudiant, on filtre ses soumissions
    if is_student:
        submissions = Submission.objects.filter(assignment=assignment, student=request.user)
    elif is_teacher and course.teacher == request.user:
        # Si l'utilisateur est l'enseignant du cours, il peut voir toutes les soumissions
        submissions = Submission.objects.filter(assignment=assignment)
    elif request.user.is_superuser:
        # Si l'utilisateur est un superuser, il peut voir toutes les soumissions
        submissions = Submission.objects.filter(assignment=assignment)
    else:
        messages.error(request, "Vous n'avez pas les permissions nécessaires pour accéder à cette page.")
        return redirect('courses:course_list')

    context = {
        'course': course,
        'assignment': assignment,
        'submissions': submissions,
    }

    return render(request, 'courses/submission_list.html', context)


@login_required
def validate_submission(request, course_pk, assignment_pk, submission_pk):
    """Vue pour valider ou rejeter une soumission"""
    # Récupérer les objets nécessaires
    course = get_object_or_404(Course, pk=course_pk)
    assignment = get_object_or_404(Assignment, pk=assignment_pk, course=course)
    submission = get_object_or_404(Submission, pk=submission_pk, assignment=assignment)

    # Vérifier que l'utilisateur est l'enseignant du cours ou un administrateur
    is_teacher = hasattr(request.user, 'is_teacher') and request.user.is_teacher
    if not (is_teacher and course.teacher == request.user) and not request.user.is_superuser:
        messages.error(request, "Vous n'avez pas les permissions nécessaires pour effectuer cette action.")
        return redirect('courses:submission_list', course_pk=course_pk, assignment_pk=assignment_pk)

    if request.method == 'POST':
        action = request.POST.get('action')

        # Récupérer les données du formulaire
        grade = request.POST.get('grade')
        feedback = request.POST.get('feedback')

        # Mettre à jour la note si fournie
        grade_value = None
        if grade:
            try:
                grade_value = float(grade)
                submission.grade = grade_value
            except ValueError:
                messages.warning(request, "La note fournie n'est pas valide. Elle n'a pas été mise à jour.")

        # Mettre à jour le feedback
        if feedback:
            submission.feedback = feedback

        if action == 'validate':
            submission.status = 'validated'
            submission.validated_at = timezone.now()
            submission.validated_by = request.user
            submission.save()
            messages.success(request, f"La soumission de {submission.student.get_full_name()} a été validée.")

        elif action == 'reject':
            submission.status = 'rejected'
            submission.validated_at = timezone.now()
            submission.validated_by = request.user
            submission.save()
            messages.success(request, f"La soumission de {submission.student.get_full_name()} a été rejetée.")

        elif action == 'grade':
            # Déterminer automatiquement le statut en fonction de la note
            if grade_value is not None:
                if grade_value >= 10:
                    submission.status = 'validated'
                    status_msg = "validée"
                else:
                    submission.status = 'rejected'
                    status_msg = "non validée"

                submission.validated_at = timezone.now()
                submission.validated_by = request.user
                submission.save()
                messages.success(request, f"La soumission de {submission.student.get_full_name()} a été notée {grade_value}/20 et {status_msg}.")
            else:
                messages.error(request, "Vous devez fournir une note pour évaluer la soumission.")

        elif action == 'feedback':
            # Mettre à jour uniquement le feedback
            if feedback:
                submission.feedback = feedback
                submission.save()
                messages.success(request, f"Le commentaire pour la soumission de {submission.student.get_full_name()} a été mis à jour.")
            else:
                submission.feedback = ""
                submission.save()
                messages.success(request, f"Le commentaire pour la soumission de {submission.student.get_full_name()} a été supprimé.")

    return redirect('courses:submission_list', course_pk=course_pk, assignment_pk=assignment_pk)


@login_required
def student_grades(request):
    """Vue pour afficher les notes d'un étudiant pour toutes ses soumissions"""
    if not hasattr(request.user, 'is_student') or not request.user.is_student:
        messages.error(request, "Cette page est réservée aux étudiants.")
        return redirect('home')

    # Récupérer toutes les soumissions de l'étudiant
    submissions = Submission.objects.filter(student=request.user).order_by('-submitted_at')

    # Organiser les soumissions par cours
    courses_data = {}

    for submission in submissions:
        course = submission.assignment.course

        if course.id not in courses_data:
            courses_data[course.id] = {
                'course': course,
                'submissions': [],
                'average_grade': 0,
                'validated_count': 0,
                'rejected_count': 0,
                'pending_count': 0,
                'total_submissions': 0
            }

        courses_data[course.id]['submissions'].append(submission)
        courses_data[course.id]['total_submissions'] += 1

        if submission.status == 'validated':
            courses_data[course.id]['validated_count'] += 1
        elif submission.status == 'rejected':
            courses_data[course.id]['rejected_count'] += 1
        else:
            courses_data[course.id]['pending_count'] += 1

    # Calculer la moyenne des notes pour chaque cours
    for course_id, data in courses_data.items():
        graded_submissions = [s for s in data['submissions'] if s.grade is not None]
        if graded_submissions:
            total_grade = sum(float(s.grade) for s in graded_submissions)
            data['average_grade'] = round(total_grade / len(graded_submissions), 2)

    context = {
        'courses_data': courses_data.values(),
        'total_submissions': submissions.count(),
        'graded_submissions': submissions.exclude(grade=None).count(),
        'validated_submissions': submissions.filter(status='validated').count(),
        'rejected_submissions': submissions.filter(status='rejected').count(),
        'pending_submissions': submissions.filter(status='pending').count(),
    }

    return render(request, 'courses/student_grades.html', context)