from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from django.conf import settings

class Client(models.Model):
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['name']),
        ]

class Project(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=[('active', 'Active'), ('completed', 'Completed')])
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['client', 'status']),  
        ]

class Task(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    assignee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('completed', 'Completed')])
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['assignee']),
            models.Index(fields=['project', 'status']), 
            models.Index(fields=['-created_at']),  # For ordering
        ]

@receiver([post_save, post_delete], sender=Project)
@receiver([post_save, post_delete], sender=Task)
def invalidate_dashboard_cache(sender, instance, **kwargs):
    """Invalidate cache when project or task data changes"""
    if sender == Project:
        client_id = instance.client.id
    else:  # Task
        client_id = instance.project.client.id
    
    cache_keys = [
        f"dashboard_client_{client_id}",
        f"advanced_dashboard_client_{client_id}"
    ]
    cache.delete_many(cache_keys)