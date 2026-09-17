from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Course, Lesson, CourseAssignment
from datetime import date, timedelta

class Command(BaseCommand):
    help = 'Seeds global superuser and initial foundational training course'

    def handle(self, *args, **options):
        # 1. Seed Global Admin
        admin_user = 'prabhakarjee'
        admin_email = 'prabhakarjha@loansemporium.com'
        admin_pass = '9Q6Ovhb5QR0IY69AphI8wIbe'

        if not User.objects.filter(username=admin_user).exists():
            User.objects.create_superuser(
                username=admin_user,
                email=admin_email,
                password=admin_pass,
                first_name='Prabhakar',
                last_name='Jha'
            )
            self.stdout.write(self.style.SUCCESS(f"✅ Created superuser: {admin_user}"))
        else:
            self.stdout.write(f"ℹ️ Superuser {admin_user} already exists.")

        # 2. Seed Sample Employee
        emp_user, created = User.objects.get_or_create(
            username='sundarjha',
            defaults={
                'email': 'sundarjha@loansemporium.com',
                'first_name': 'Sundar',
                'last_name': 'Jha'
            }
        )
        if created:
            emp_user.set_password('Sovereign123!')
            emp_user.save()
            self.stdout.write(self.style.SUCCESS("✅ Created sample employee: sundarjha"))

        # 3. Seed Course 1: Onboarding & Compliance
        course, c_created = Course.objects.get_or_create(
            slug='onboarding-compliance-fundamentals',
            defaults={
                'title': 'Loans Emporium — Onboarding & Compliance Fundamentals',
                'description': 'Essential regulatory, KYC, AML, and credit security principles for all corporate personnel.',
                'icon': '🛡️',
                'estimated_hours': 2,
                'is_published': True
            }
        )

        Lesson.objects.get_or_create(
            course=course,
            slug='introduction-sovereign-mission',
            defaults={
                'title': '1. Sovereign Mission & Institutional Ethics',
                'content': """# Welcome to Loans Emporium

Loans Emporium operates under Sovereign institutional principles. Our mission is to provide transparent, frictionless, and secure credit access to verified borrowers.

### Core Ethical Standards
- **Integrity**: Full transparency in loan terms, fees, and disclosure schedules.
- **Privacy & Security**: Zero tolerance for unauthorized disclosure of customer PII (Personally Identifiable Information).
- **Compliance First**: Strict adherence to RBI, AML (Anti-Money Laundering), and KYC guidelines.""",
                'order': 1,
                'estimated_minutes': 15
            }
        )

        Lesson.objects.get_or_create(
            course=course,
            slug='kyc-aml-compliance',
            defaults={
                'title': '2. KYC & AML Compliance Checklist',
                'content': """# KYC & Anti-Money Laundering Playbook

Every loan application processed must satisfy primary identity verification standards before credit underwriting.

### Mandatory Documents Checklist
1. **Primary ID**: Aadhaar / PAN / Passport (verified against government databases).
2. **Income Verification**: 6 months verified bank statement and latest ITR or payslip.
3. **Address Verification**: Utility bill or rental agreement not older than 90 days.

### Red Flags to Report
- Discrepancy between borrower name and bank account holder name.
- Multiple rapid micro-loan requests from unrelated applicants using identical IP or device fingerprints.
- Immediate requests for cash-equivalent disbursements.""",
                'order': 2,
                'estimated_minutes': 25
            }
        )

        Lesson.objects.get_or_create(
            course=course,
            slug='information-security-policy',
            defaults={
                'title': '3. Information Security & Data Protection',
                'content': """# Corporate Information Security Policy

All borrower data stored across Loans Emporium infrastructure is protected by Dark Mesh encryption.

### Staff Security Responsibilities
- Always access internal platforms via **Authentik SSO** with Multi-Factor Authentication.
- Never export customer financial data to personal devices or unsecured cloud drives.
- Immediately report lost corporate credentials to `security@loansemporium.com`.""",
                'order': 3,
                'estimated_minutes': 20
            }
        )

        # 4. Assign course to sample employee with 7-day deadline
        CourseAssignment.objects.get_or_create(
            user=emp_user,
            course=course,
            defaults={
                'assigned_by': User.objects.get(username=admin_user),
                'deadline': date.today() + timedelta(days=7),
                'status': 'assigned',
            }
        )

        self.stdout.write(self.style.SUCCESS("✅ Seeded initial course and assignment!"))
