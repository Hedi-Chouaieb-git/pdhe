from django.db import models

# Create your models here.
from django.db import models
from django.conf import settings
from django.utils import timezone
import secrets
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.
class Course(models.Model):
    LEVEL_CHOICES = [
        ('L1', 'Licence 1'),
        ('L2', 'Licence 2'),
        ('L3', 'Licence 3'),
        ('M1', 'Master 1'),
        ('M2', 'Master 2'),
    ]

    title = models.CharField(max_length=200, verbose_name="Nom du cours")
    description = models.TextField(verbose_name="Description")
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='courses')
    level = models.CharField(max_length=2, choices=LEVEL_CHOICES, default='L1', verbose_name="Niveau du cours")
    access_key = models.CharField(max_length=10, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    enrolled_students = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='enrolled_courses', blank=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class Resource(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='resources')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='course_resources/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.course.title}"

class Assignment(models.Model):
    ASSIGNMENT_TYPES = (
        ('TP', 'Travail Pratique'),
        ('TD', 'Travail Dirigé'),
    )

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=200)
    description = models.TextField()
    assignment_type = models.CharField(max_length=2, choices=ASSIGNMENT_TYPES)
    due_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resources = models.ManyToManyField(Resource, blank=True, related_name='assignments')
    file = models.FileField(upload_to='assignments/', blank=True, null=True)

    def __str__(self):
        return f"{self.get_assignment_type_display()} - {self.title}"

class Submission(models.Model):
    STATUS_CHOICES = [
        ('pending', 'À vérifier'),
        ('validated', 'Validé'),
        ('rejected', 'Non validé'),
    ]

    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='submissions')
    file = models.FileField(upload_to='submissions/')
    submitted_at = models.DateTimeField(auto_now_add=True)
    grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Statut")
    validated_at = models.DateTimeField(null=True, blank=True)
    validated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='validated_submissions'
    )

    class Meta:
        unique_together = ('assignment', 'student')

    def __str__(self):
        return f"{self.student.username} - {self.assignment.title}"

class Payments(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('student', 'course')

    def __str__(self):
        return f"{self.student.username} - {self.course.title}"


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'En retard'),
        ('excused', 'Excusé'),
    ]

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='attendance_records')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='attendance_records')
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='taught_attendance')
    date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='present')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Présence'
        verbose_name_plural = 'Présences'
        ordering = ['-date', 'student__last_name']
        unique_together = ('student', 'course', 'date')

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.course.title} - {self.get_status_display()} - {self.date}"

    def save(self, *args, **kwargs):
        # Auto-set the teacher to the course's teacher if not set
        if not self.teacher and self.course:
            self.teacher = self.course.teacher
        super().save(*args, **kwargs)
