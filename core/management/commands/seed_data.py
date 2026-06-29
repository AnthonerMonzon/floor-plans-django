from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from core.models import Project


class Command(BaseCommand):
    help = "Seed the database with a demo user and sample projects."

    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(
            username="admin@example.com",
            defaults={
                "email": "admin@example.com",
                "first_name": "Admin",
                "last_name": "User",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            user.set_password("admin123")
            user.save()
            self.stdout.write(self.style.SUCCESS("Created admin user: admin@example.com / admin123"))
        else:
            self.stdout.write(self.style.WARNING("Admin user already exists."))

        user.profile.first_name = "Admin"
        user.profile.last_name = "User"
        user.profile.role = "admin"
        user.profile.save()

        if Project.objects.count() == 0:
            Project.objects.create(
                project_name="Downtown Medical Center",
                project_code="DMC-2026-001",
                client_name="City Health Dept",
                project_address="123 Main St, Downtown",
                status="active",
                created_by=user,
            )
            Project.objects.create(
                project_name="Westside Blood Bank",
                project_code="WBB-2026-002",
                client_name="Regional Blood Services",
                project_address="456 West Ave",
                status="draft",
                created_by=user,
            )
            self.stdout.write(self.style.SUCCESS("Created sample projects."))
        else:
            self.stdout.write(self.style.WARNING("Projects already exist."))
