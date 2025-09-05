from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Prefetch
from .serializers import ClientSerializer
from rest_framework.permissions import IsAuthenticated
from .models import Client, Project, Task, Comment
from .serializers import (
    ProjectListSerializer,
    ProjectDetailSerializer,
    ProjectCreateSerializer,
    TaskListSerializer,
    TaskDetailSerializer,
    TaskCreateSerializer,
    CommentSerializer,
    CommentCreateSerializer
)
from .permissions import MultiTenantPermission

class ProjectViewSet(viewsets.ModelViewSet):
    """
    Projects ViewSet under a client:
    GET    /api/clients/{client_id}/projects/
    POST   /api/clients/{client_id}/projects/
    GET    /api/clients/{client_id}/projects/{id}/
    PUT    /api/clients/{client_id}/projects/{id}/
    DELETE /api/clients/{client_id}/projects/{id}/
    """
    permission_classes = [permissions.IsAuthenticated, MultiTenantPermission]
    permission_object_attr = 'client'

    def get_client(self):
        client_id = self.kwargs.get("client_pk")  # ✅ nested router key
        client = get_object_or_404(Client, id=client_id, is_deleted=False)
        # Optional: permission check
        if not client.memberships.filter(user=self.request.user, is_active=True).exists():
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You do not have access to this client.")
        return client

    def get_queryset(self):
        client = self.get_client()
        return Project.objects.filter(client=client).select_related(
            "created_by", "updated_by", "client"
        ).prefetch_related(
            Prefetch("tasks")
        )

    def get_serializer_class(self):
        if self.action == "list":
            return ProjectListSerializer
        elif self.action in ["retrieve"]:
            return ProjectDetailSerializer
        elif self.action in ["create"]:
            return ProjectCreateSerializer
        return ProjectDetailSerializer

    def perform_create(self, serializer):
        client = self.get_client()
        serializer.context['client'] = client
        serializer.save(client=client, created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def destroy(self, request, *args, **kwargs):
        project = self.get_object()
        project.delete()  # soft delete
        return Response(status=status.HTTP_204_NO_CONTENT)

class TaskViewSet(viewsets.ModelViewSet):
    """
    Tasks ViewSet under a project:
    GET    /api/clients/{client_id}/projects/{project_id}/tasks/
    POST   /api/clients/{client_id}/projects/{project_id}/tasks/
    GET    /api/clients/{client_id}/projects/{project_id}/tasks/{id}/
    PUT    /api/clients/{client_id}/projects/{project_id}/tasks/{id}/
    DELETE /api/clients/{client_id}/projects/{project_id}/tasks/{id}/
    """
    permission_classes = [permissions.IsAuthenticated, MultiTenantPermission]
    permission_object_attr = 'project'

    def get_project(self):
        client_id = self.kwargs.get("client_pk")
        project_id = self.kwargs.get("project_pk")  # nested router key
        project = get_object_or_404(
            Project,
            id=project_id,
            client_id=client_id,
            is_deleted=False
        )
        if not project.client.users.filter(id=self.request.user.id).exists():
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You do not have access to this project.")
        return project

    def get_queryset(self):
        project = self.get_project()
        return Task.objects.filter(project=project).select_related(
            "project", "created_by", "updated_by"
        ).prefetch_related(
            "assignees", "comments"
        )

    def get_serializer_class(self):
        if self.action == "list":
            return TaskListSerializer
        elif self.action in ["retrieve"]:
            return TaskDetailSerializer
        elif self.action in ["create"]:
            return TaskCreateSerializer
        return TaskDetailSerializer

    def perform_create(self, serializer):
        project = self.get_project()
        serializer.context['project'] = project
        serializer.save(project=project, created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def destroy(self, request, *args, **kwargs):
        task = self.get_object()
        task.delete()  # soft delete
        return Response(status=status.HTTP_204_NO_CONTENT)

class CommentViewSet(viewsets.ModelViewSet):
    """
    Comments ViewSet under a task:
    GET    /api/client/{client_id}/project/{project_id}/tasks/{task_id}/comments/
    POST   /api/client/{client_id}/project/{project_id}/tasks/{task_id}/comments/
    GET    /api/client/{client_id}/project/{project_id}/tasks/{task_id}/comments/{id}/
    PUT    /api/client/{client_id}/project/{project_id}/tasks/{task_id}/comments/{id}/
    DELETE /api/client/{client_id}/project/{project_id}/tasks/{task_id}/comments/{id}/
    """
    permission_classes = [permissions.IsAuthenticated, MultiTenantPermission]
    permission_object_attr = 'task'

    def get_task(self):
        client_id = self.kwargs.get("client_pk")
        project_id = self.kwargs.get("project_pk")
        task_id = self.kwargs.get("task_pk")  # <--- nested router key
        task = get_object_or_404(
            Task,
            id=task_id,
            project_id=project_id,
            project__client_id=client_id,
            is_deleted=False
        )
        if not task.project.client.users.filter(id=self.request.user.id).exists():
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You do not have access to this task.")
        return task

    def get_queryset(self):
        task = self.get_task()
        return Comment.objects.filter(task=task).select_related("author")

    def get_serializer_class(self):
        if self.action == "create":
            return CommentCreateSerializer
        return CommentSerializer

    def perform_create(self, serializer):
        task = self.get_task()
        serializer.context['task'] = task
        serializer.context['request'] = self.request
        serializer.save()

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        comment.delete()  # soft delete
        return Response(status=status.HTTP_204_NO_CONTENT)
    

class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticated]