from django.contrib import admin
from .models import Course, Lesson, CourseAssignment, LessonProgress

class LessonInline(admin.StackedInline):
    model = Lesson
    extra = 1

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'estimated_hours', 'is_published', 'total_lessons', 'created_at')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [LessonInline]

@admin.register(CourseAssignment)
class CourseAssignmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'deadline', 'status', 'progress_percentage', 'is_overdue', 'escalation_stage')
    list_filter = ('status', 'course', 'deadline')
    search_fields = ('user__username', 'user__email', 'course__title')

@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'lesson', 'is_completed', 'completed_at')
