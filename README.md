# 🛡️ Loans Emporium Learning Platform (Sovereign Django LMS)

A bespoke, lightweight institutional learning and compliance tracking application designed specifically for Loans Emporium operations under the Sovereign Fleet.

## Features
- **Minimalist Architecture**: Focuses strictly on Admin, User, Course, and Deadline tracking.
- **Many-to-Many Course Assignments**: Assign multiple courses to learners independently with distinct deadlines.
- **Zero-Click Authentik SSO**: Header-based authentication (`X-Authentik-Email`) via Caddy Reverse Proxy.
- **Automated Deadline Escalations**: 2-tier escalation with automated email notifications to Learners and direct alerts to the Global Administrator.
- **Executive Compliance Matrix**: Real-time compliance monitoring, employee progress bars, nudge buttons, and one-click CSV export for audits.
- **AI Course Builder**: Synthesizes internal SOP policy documents into structured 3-module courses.

## Deployment
Managed declaratively via Sovereign Citadel:
```bash
./Citadel/ctl app deploy lms
```
