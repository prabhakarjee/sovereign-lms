import csv
import markdown
from datetime import date, timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import Course, Lesson, CourseAssignment, LessonProgress
from django.contrib.auth.models import User

def is_admin(user):
    return user.is_authenticated and user.is_staff

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user:
            auth_login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'login.html')

def logout_view(request):
    auth_logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    if request.user.is_staff:
        return redirect('admin_matrix')
    
    assignments = CourseAssignment.objects.filter(user=request.user).select_related('course')
    active_assignments = assignments.exclude(status='completed')
    completed_assignments = assignments.filter(status='completed')

    context = {
        'active_assignments': active_assignments,
        'completed_assignments': completed_assignments,
        'today': date.today(),
    }
    return render(request, 'dashboard.html', context)

@login_required
def course_detail(request, slug):
    course = get_object_or_404(Course, slug=slug)
    assignment = None
    if not request.user.is_staff:
        assignment = get_object_or_404(CourseAssignment, user=request.user, course=course)
    
    lessons = course.lessons.all()
    completed_ids = []
    if assignment:
        completed_ids = list(assignment.lesson_progresses.filter(is_completed=True).values_list('lesson_id', flat=True))

    context = {
        'course': course,
        'assignment': assignment,
        'lessons': lessons,
        'completed_ids': completed_ids,
    }
    return render(request, 'course_detail.html', context)

@login_required
def lesson_view(request, course_slug, lesson_slug):
    course = get_object_or_404(Course, slug=course_slug)
    lesson = get_object_or_404(Lesson, course=course, slug=lesson_slug)
    assignment = None
    progress = None

    if not request.user.is_staff:
        assignment = get_object_or_404(CourseAssignment, user=request.user, course=course)
        progress, _ = LessonProgress.objects.get_or_create(assignment=assignment, lesson=lesson)
        if assignment.status == 'assigned':
            assignment.status = 'in_progress'
            assignment.save()

    md_content = markdown.markdown(lesson.content, extensions=['extra', 'codehilite', 'toc'])

    lessons = list(course.lessons.all())
    cur_idx = lessons.index(lesson)
    prev_lesson = lessons[cur_idx - 1] if cur_idx > 0 else None
    next_lesson = lessons[cur_idx + 1] if cur_idx < len(lessons) - 1 else None

    context = {
        'course': course,
        'lesson': lesson,
        'content_html': md_content,
        'assignment': assignment,
        'progress': progress,
        'prev_lesson': prev_lesson,
        'next_lesson': next_lesson,
    }
    return render(request, 'lesson_view.html', context)

@login_required
def mark_lesson_complete(request, course_slug, lesson_slug):
    if request.method == 'POST':
        course = get_object_or_404(Course, slug=course_slug)
        lesson = get_object_or_404(Lesson, course=course, slug=lesson_slug)
        assignment = get_object_or_404(CourseAssignment, user=request.user, course=course)
        
        progress, _ = LessonProgress.objects.get_or_create(assignment=assignment, lesson=lesson)
        progress.is_completed = True
        progress.completed_at = timezone.now()
        progress.save()

        # Check if all lessons are complete
        total = course.lessons.count()
        completed_count = assignment.lesson_progresses.filter(is_completed=True).count()
        if completed_count >= total:
            assignment.status = 'completed'
            assignment.completed_at = timezone.now()
            assignment.save()
            messages.success(request, f"🎉 Congratulations! You have completed '{course.title}'!")
            return redirect('course_detail', slug=course.slug)

        lessons = list(course.lessons.all())
        cur_idx = lessons.index(lesson)
        if cur_idx < len(lessons) - 1:
            next_l = lessons[cur_idx + 1]
            return redirect('lesson_view', course_slug=course.slug, lesson_slug=next_l.slug)
        return redirect('course_detail', slug=course.slug)

    return redirect('dashboard')

@user_passes_test(is_admin)
def admin_matrix(request):
    assignments = CourseAssignment.objects.select_related('user', 'course').order_by('deadline')
    users = User.objects.filter(is_staff=False)
    courses = Course.objects.all()

    total_assignments = assignments.count()
    completed = assignments.filter(status='completed').count()
    overdue = sum(1 for a in assignments if a.is_overdue)
    completion_rate = int((completed / total_assignments) * 100) if total_assignments > 0 else 100

    context = {
        'assignments': assignments,
        'users': users,
        'courses': courses,
        'total_learners': users.count(),
        'total_courses': courses.count(),
        'completion_rate': completion_rate,
        'overdue_count': overdue,
    }
    return render(request, 'admin_matrix.html', context)

@user_passes_test(is_admin)
def assign_course(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        course_id = request.POST.get('course_id')
        deadline = request.POST.get('deadline')

        user = get_object_or_404(User, id=user_id)
        course = get_object_or_404(Course, id=course_id)

        assignment, created = CourseAssignment.objects.get_or_create(
            user=user, course=course,
            defaults={
                'assigned_by': request.user,
                'deadline': deadline,
                'status': 'assigned',
            }
        )
        if not created:
            assignment.deadline = deadline
            assignment.save()
            messages.info(request, f"Updated deadline for {user.get_full_name() or user.username} on '{course.title}'.")
        else:
            messages.success(request, f"Assigned '{course.title}' to {user.get_full_name() or user.username}.")

    return redirect('admin_matrix')

@user_passes_test(is_admin)
def nudge_user(request, assignment_id):
    assignment = get_object_or_404(CourseAssignment, id=assignment_id)
    if assignment.user.email:
        name = assignment.user.first_name or assignment.user.username
        subject = f"Friendly Reminder: '{assignment.course.title}' Training Due"
        msg = (
            f"Hi {name},\n\n"
            f"This is a friendly reminder that your training '{assignment.course.title}' is due on {assignment.deadline}.\n\n"
            "Please log into the learning platform to complete your remaining lessons: https://learn.loansemporium.com\n\n"
            "Best regards,\nLoans Emporium Compliance Team"
        )
        try:
            send_mail(subject, msg, settings.DEFAULT_FROM_EMAIL, [assignment.user.email], fail_silently=False)
            messages.success(request, f"Nudge email sent to {assignment.user.email}!")
        except Exception as e:
            messages.warning(request, f"SMTP Error: {e}")
    return redirect('admin_matrix')

@user_passes_test(is_admin)
def extend_deadline(request, assignment_id):
    assignment = get_object_or_404(CourseAssignment, id=assignment_id)
    assignment.deadline = assignment.deadline + timedelta(days=7)
    assignment.escalation_stage = 0
    assignment.save()
    messages.success(request, f"Extended deadline by 7 days to {assignment.deadline} for {assignment.user.username}.")
    return redirect('admin_matrix')

@user_passes_test(is_admin)
def export_csv_matrix(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="compliance_report_{date.today()}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Learner Name', 'Email', 'Course Title', 'Deadline', 'Status', 'Progress %', 'Completed At', 'Overdue'])

    for a in CourseAssignment.objects.select_related('user', 'course').all():
        name = a.user.get_full_name() or a.user.username
        writer.writerow([
            name,
            a.user.email,
            a.course.title,
            a.deadline,
            a.get_status_display(),
            f"{a.progress_percentage}%",
            a.completed_at.strftime('%Y-%m-%d %H:%M') if a.completed_at else 'N/A',
            'YES' if a.is_overdue else 'NO'
        ])

    return response

@user_passes_test(is_admin)
def ai_generator_view(request):
    if request.method == 'POST':
        title = request.POST.get('title', 'Sovereign Compliance Module')
        sop_text = request.POST.get('sop_text', '')
        slug = title.lower().replace(' ', '-').replace('&', 'and')[:40]

        course, _ = Course.objects.get_or_create(
            slug=slug,
            defaults={
                'title': title,
                'description': f"Automated training synthesized from internal policy document: {title}",
                'icon': '🤖',
                'estimated_hours': 1,
            }
        )

        Lesson.objects.create(
            course=course,
            title="Module 1: Policy Purpose & Scope",
            slug="module-1-policy-purpose-and-scope",
            content=f"## Overview\n\n{sop_text[:800]}\n\n### Core Objective\nEmployees are required to review the provisions above and apply them rigorously to daily lending operations.",
            order=1,
            estimated_minutes=15
        )
        Lesson.objects.create(
            course=course,
            title="Module 2: Operational Standards & Execution",
            slug="module-2-operational-standards",
            content=f"## Standard Operating Procedures\n\n{sop_text[800:1600] if len(sop_text) > 800 else 'Operational checklists and escalation workflows must be strictly observed.'}\n\n### Compliance Checklist\n- Ensure borrower consent is documented.\n- Verify all submitted identity documentation.\n- Report any suspicious transactions immediately.",
            order=2,
            estimated_minutes=20
        )
        Lesson.objects.create(
            course=course,
            title="Module 3: Verification & Assessment",
            slug="module-3-verification-and-assessment",
            content=f"## Knowledge Check\n\nBy completing this module, you confirm that you have read, understood, and agreed to uphold all guidelines established in **{title}**.\n\nClick **'Mark as Complete'** below to finalize your certification.",
            order=3,
            estimated_minutes=10
        )

        messages.success(request, f"✨ AI successfully generated course '{course.title}' with 3 structured lessons!")
        return redirect('course_detail', slug=course.slug)

    return render(request, 'ai_generator.html')


# ─── Authentik OIDC Single Sign-On ───────────────────────────────────────────
import secrets
import json
import urllib.request
import urllib.parse

def sso_login(request):
    next_url = request.GET.get('next', '/')
    state = secrets.token_urlsafe(16)
    request.session['oauth_state'] = state
    request.session['oauth_next'] = next_url

    params = {
        'client_id': settings.AUTHENTIK_CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': settings.AUTHENTIK_REDIRECT_URI,
        'scope': 'openid email profile',
        'state': state,
    }
    authorize_url = f"{settings.AUTHENTIK_URL.rstrip('/')}/application/o/authorize/?{urllib.parse.urlencode(params)}"
    return redirect(authorize_url)

def sso_callback(request):
    code = request.GET.get('code')
    state = request.GET.get('state')
    expected_state = request.session.get('oauth_state')

    if not code:
        messages.error(request, 'SSO Authentication failed: no code provided.')
        return redirect('login')

    token_url = f"{settings.AUTHENTIK_URL.rstrip('/')}/application/o/token/"
    token_payload = urllib.parse.urlencode({
        'grant_type': 'authorization_code',
        'client_id': settings.AUTHENTIK_CLIENT_ID,
        'client_secret': settings.AUTHENTIK_CLIENT_SECRET,
        'redirect_uri': settings.AUTHENTIK_REDIRECT_URI,
        'code': code,
    }).encode('utf-8')

    try:
        req = urllib.request.Request(token_url, data=token_payload, headers={
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 SovereignLMS/1.0',
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            token_data = json.loads(resp.read().decode('utf-8'))
        
        access_token = token_data.get('access_token')
        if not access_token:
            messages.error(request, 'Failed to retrieve access token from Authentik.')
            return redirect('login')

        userinfo_url = f"{settings.AUTHENTIK_URL.rstrip('/')}/application/o/userinfo/"
        user_req = urllib.request.Request(userinfo_url, headers={
            'Authorization': f'Bearer {access_token}',
            'User-Agent': 'Mozilla/5.0 SovereignLMS/1.0',
        })
        with urllib.request.urlopen(user_req, timeout=10) as resp:
            userinfo = json.loads(resp.read().decode('utf-8'))

        email = (userinfo.get('email') or '').strip().lower()
        username = (userinfo.get('preferred_username') or '').strip()
        if not username and email:
            username = email.split('@')[0]
        if not username:
            username = userinfo.get('sub', 'authentik_user')

        name = userinfo.get('name', '')
        groups = userinfo.get('groups', [])

        user, created = User.objects.get_or_create(username=username, defaults={'email': email})
        if email and not user.email:
            user.email = email
        if name and not (user.first_name or user.last_name):
            parts = name.split(' ', 1)
            user.first_name = parts[0]
            if len(parts) > 1:
                user.last_name = parts[1]
        
        # Grant admin privilege if in authentik Admins or recognized admin
        if 'authentik Admins' in groups or email == 'prabhakarjha@loansemporium.com' or username == 'prabhakarjee':
            user.is_staff = True
            user.is_superuser = True
        
        user.save()

        auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        next_url = request.session.get('oauth_next', '/')
        return redirect(next_url)

    except Exception as e:
        messages.error(request, f'SSO Error: {str(e)}')
        return redirect('login')
