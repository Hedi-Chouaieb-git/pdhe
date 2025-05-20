from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('', views.CourseListView.as_view(), name='course_list'),
    path('course/<int:pk>/', views.CourseDetailView.as_view(), name='course_detail'),
    path('course/create/', views.CourseCreateView.as_view(), name='course_create'),
    path('course/<int:pk>/update/', views.CourseUpdateView.as_view(), name='course_update'),
    path('course/<int:pk>/delete/', views.CourseDeleteView.as_view(), name='course_delete'),
    path('enroll/<int:pk>/', views.enroll_course, name='enroll_course'),
    path('course/<int:pk>/unroll/', views.unroll_course, name='unroll_course'),
    path('mes-cours/', views.student_courses, name='student_courses'),
    # URLs pour les ressources
    path('course/<int:course_pk>/resource/create/', views.ResourceCreateView.as_view(), name='resource_create'),
    path('course/<int:course_pk>/assignment/create/', views.AssignmentCreateView.as_view(), name='assignment_create'),
    path('course/<int:course_pk>/assignment/<int:assignment_pk>/submit/',
         views.SubmissionCreateView.as_view(), name='submission_create'),
         # Suppression de ressource et TP/TD
    path('course/<int:course_pk>/resource/<int:pk>/delete/', views.delete_resource, name='resource_delete'),
    path('course/<int:course_pk>/assignment/<int:pk>/delete/', views.delete_assignment, name='assignment_delete'),
    path('course/<int:course_pk>/assignment/<int:assignment_pk>/submissions/', views.submission_list, name='submission_list'),
    path('course/<int:course_pk>/students/', views.course_students_list, name='course_students_list'),
    path('course/<int:course_pk>/assignment/<int:assignment_pk>/submission/<int:submission_pk>/validate/',
         views.validate_submission, name='validate_submission'),
    path('student/grades/', views.student_grades, name='student_grades'),
]