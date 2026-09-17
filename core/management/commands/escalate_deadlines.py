from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from core.models import CourseAssignment
from datetime import date

class Command(BaseCommand):
    help = 'Evaluates course deadlines, sends employee reminders, and escalates breaches to the Admin'

    def handle(self, *args, **options):
        today = date.today()
        assignments = CourseAssignment.objects.filter(status__in=['assigned', 'in_progress'])

        for a in assignments:
            days_left = (a.deadline - today).days

            # Tier 1: T - 2 Days Reminder
            if days_left <= 2 and days_left >= 0 and a.escalation_stage == 0:
                if a.user.email:
                    subject = f"Reminder: '{a.course.title}' is due in {days_left} days"
                    body = f"Hi {a.user.first_name or a.user.username},\n\nYour assigned course '{a.course.title}' is scheduled for completion by {a.deadline}.\n\nPlease complete your pending lessons here:\nhttps://learn.loansemporium.com/course/{a.course.slug}/\n\nRegards,\nLoans Emporium Compliance"
                    try:
                        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [a.user.email], fail_silently=True)
                        a.escalation_stage = 1
                        a.save()
                        self.stdout.write(self.style.SUCCESS(f"Sent Tier 1 reminder to {a.user.email}"))
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"SMTP error: {e}"))

            # Tier 2: Deadline Breached -> Escalation to Admin & User
            elif days_left < 0 and a.escalation_stage < 2:
                # 1. Alert Learner
                if a.user.email:
                    subject = f"URGENT: Training Deadline Overdue — '{a.course.title}'"
                    body = f"Hi {a.user.first_name or a.user.username},\n\nYour training deadline for '{a.course.title}' expired on {a.deadline} ({abs(days_left)} days ago).\n\nThis compliance breach has been flagged to the system administrator.\nPlease finish the course immediately:\nhttps://learn.loansemporium.com/course/{a.course.slug}/"
                    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [a.user.email], fail_silently=True)

                # 2. Alert Global Admin
                admin_subject = f"🚨 Compliance Escalation: {a.user.get_full_name() or a.user.username} overdue on '{a.course.title}'"
                admin_body = f"Global Administrator Alert:\n\nEmployee: {a.user.get_full_name() or a.user.username} ({a.user.email})\nCourse: {a.course.title}\nDeadline: {a.deadline} (Overdue by {abs(days_left)} days)\nCurrent Progress: {a.progress_percentage}%\n\nReview live compliance roster: https://learn.loansemporium.com/admin/matrix/"
                try:
                    send_mail(admin_subject, admin_body, settings.DEFAULT_FROM_EMAIL, [settings.ADMIN_ALERT_EMAIL], fail_silently=True)
                    a.escalation_stage = 2
                    a.save()
                    self.stdout.write(self.style.ERROR(f"Dispatched Tier 2 escalation to Admin for {a.user.username}"))
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"SMTP error: {e}"))
