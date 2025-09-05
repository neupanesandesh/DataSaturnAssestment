from django.db import models
import uuid
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import AbstractUser

class softdeleteset(models.QuerySet):
    def delete(self):
        return super().update(deleted_at=timezone.now())

    def hard_delete(self):
        return super().delete()

    def alive(self):
        return self.filter(deleted_at=None)

    def dead(self):
        return self.exclude(deleted_at=None)
    
class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return softdeleteset(self.model, using=self._db).alive()
    
    def all_with_deleted(self):
        return softdeleteset(self.model, using=self._db)
    
    def deleted_soft_only(self):
        return self.all_with_deleted().dead()
    
class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False) 
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="created_%(class)s",
        on_delete=models.SET_NULL,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="updated_%(class)s",
        on_delete=models.SET_NULL,
    )
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at", "updated_at"])

    def hard_delete(self, using=None, keep_parents=False):
        return super().delete(using=using, keep_parents=keep_parents)
    
class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    
    class Meta:
        db_table = "user"
        indexes = [
            models.Index(fields=["username"]),
            models.Index(fields=["email"]),
        ]
        
    def __str__(self):
        return self.username
    
class Client(BaseModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100, unique=True)
    default_timezone = models.CharField(max_length=50, default="UTC")
    is_active = models.BooleanField(default=True)

    users = models.ManyToManyField(
        User,
        through="ClientMembership",
        through_fields=("client", "user"), 
        related_name="clients"
    )

    class Meta:
        db_table = "client"
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return self.name
    
class ClientMembership(BaseModel):
    ROLE_CHOICES = [
        ("owner", "Owner"),
        ("admin", "Admin"),
        ("member", "Member"),
        ("viewer", "Viewer"),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="memberships")
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="member")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "client_membership"
        unique_together = (("user", "client"),)
        indexes = [
            models.Index(fields=["client", "role"]),
            models.Index(fields=["user"]),
        ]

    def __str__(self):
        return f"{self.user} @ {self.client} ({self.role})"
    
class Project(BaseModel):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("active", "Active"),
        ("completed", "Completed"),
        ("archived", "Archived"),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="projects")
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=120, null=True, blank=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "project"
        indexes = [
            models.Index(fields=["client", "name"]),
            models.Index(fields=["client", "status"]),
            models.Index(fields=["slug"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["client", "slug"], name="unique_client_project_slug")
        ]

    def __str__(self):
        return f"{self.name} ({self.client})"
    
class Task(BaseModel):
    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("urgent", "Urgent"),
    ]
    STATUS_CHOICES = [
        ("todo", "To Do"),
        ("in_progress", "In Progress"),
        ("done", "Done"),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="todo")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="medium")
    due_date = models.DateField(null=True, blank=True)
    assignees = models.ManyToManyField(User, blank=True, related_name="assigned_tasks")

    class Meta:
        db_table = "task"
        indexes = [
            models.Index(fields=["project", "status"]),
            models.Index(fields=["project", "priority"]),
            models.Index(fields=["due_date"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.project})"
    
class Comment(BaseModel):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="comments")
    content = models.TextField()

    class Meta:
        db_table = "comment"
        indexes = [
            models.Index(fields=["task", "created_at"]),
        ]

    def __str__(self):
        return f"Comment by {self.author} on {self.task}"