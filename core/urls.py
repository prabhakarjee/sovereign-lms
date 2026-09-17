from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('course/<slug:slug>/', views.course_detail, name='course_detail'),
    path('course/<slug:course_slug>/<slug:lesson_slug>/', views.lesson_view, name='lesson_view'),
    path('course/<slug:course_slug>/<slug:lesson_slug>/complete/', views.mark_lesson_complete, name='mark_lesson_complete'),
    
    # Admin Matrix & Actions
    path('admin/matrix/', views.admin_matrix, name='admin_matrix'),
    path('admin/assign/', views.assign_course, name='assign_course'),
    path('admin/nudge/<int:assignment_id>/', views.nudge_user, name='nudge_user'),
    path('admin/extend/<int:assignment_id>/', views.extend_deadline, name='extend_deadline'),
    path('admin/export/csv/', views.export_csv_matrix, name='export_csv_matrix'),
    path('admin/ai-generator/', views.ai_generator_view, name='ai_generator'),
]
