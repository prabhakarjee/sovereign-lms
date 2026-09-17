from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date

class Course(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    icon = models.CharField(max_length=50, default='📘')
    estimated_hours = models.PositiveIntegerField(default=2)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    @property
    def total_lessons(self):
        return self.lessons.count()

class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    slug = models.SlugField()
    content = models.TextField(help_text="Markdown formatted lesson material")
    order = models.PositiveIntegerField(default=1)
    estimated_minutes = models.PositiveIntegerField(default=15)
    video_url = models.URLField(blank=True, null=True)

    class Meta:
        ordering = ['order']
        unique_together = ('course', 'slug')

    def __str__(self):
        return f"{self.course.title} - {self.order}. {self.title}"

class CourseAssignment(models.Model):
    STATUS_CHOICES = [
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_assignments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_by_me')
    assigned_at = models.DateTimeField(auto_now_add=True)
    deadline = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='assigned')
    completed_at = models.DateTimeField(null=True, blank=True)
    escalation_stage = models.PositiveSmallIntegerField(default=0, help_text="0=Normal, 1=Reminder Sent, 2=Admin Escalated")

    class Meta:
        unique_together = ('user', 'course')
        ordering = ['deadline', '-assigned_at']

    def __str__(self):
        return f"{self.user.username} -> {self.course.title} ({self.status})"

    @property
    def is_overdue(self):
        if self.status == 'completed':
            return False
        return self.deadline < date.today()

    @property
    def days_remaining(self):
        diff = (self.deadline - date.today()).days
        return diff

    @property
    def progress_percentage(self):
        total = self.course.total_lessons
        if total == 0:
            return 100 if self.status == 'completed' else 0
        completed = self.lesson_progresses.filter(is_completed=True).count()
        return int((completed / total) * 100)

class LessonProgress(models.Model):
    assignment = models.ForeignKey(CourseAssignment, on_delete=models.CASCADE, related_name='lesson_progresses')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='user_progresses')
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('assignment', 'lesson')

    def __str__(self):
        return f"{self.assignment.user.username} - {self.lesson.title}: {self.is_completed}"
