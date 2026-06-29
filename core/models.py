import uuid

from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("reviewer", "Reviewer"),
        ("user", "User"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="user")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "profiles"

    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip() or self.user.username


class Project(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("active", "Active"),
        ("review", "In Review"),
        ("approved", "Approved"),
        ("archived", "Archived"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project_name = models.CharField(max_length=255)
    project_code = models.CharField(max_length=100, unique=True)
    client_name = models.CharField(max_length=255, blank=True)
    project_address = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = "projects"
        ordering = ["-created_at"]

    def __str__(self):
        return self.project_name


class FloorPlan(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("review", "In Review"),
        ("approved", "Approved"),
        ("archived", "Archived"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="floor_plans")
    file_name = models.CharField(max_length=255)
    file = models.FileField(upload_to="floor_plans/%Y/%m/%d/")
    converted_file = models.ImageField(upload_to="floor_plans/converted/%Y/%m/%d/", blank=True, null=True)
    supabase_url = models.URLField(blank=True, default="")
    version_no = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    annotate = models.JSONField(blank=True, null=True, default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "floor_plans"
        ordering = ["-version_no", "-created_at"]

    def __str__(self):
        return f"{self.project.project_name} - {self.file_name} (v{self.version_no})"
