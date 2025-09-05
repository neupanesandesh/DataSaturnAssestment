from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Client, ClientMembership, Project, Task, Comment
from django.utils import timezone

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """Basic user serializer for nested relationships."""
    
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name']
        read_only_fields = ['id']

class ClientSerializer(serializers.ModelSerializer):
    """Client serializer with basic info."""
    
    class Meta:
        model = Client
        fields = ['id', 'name', 'slug', 'default_timezone', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']

class ClientMembershipSerializer(serializers.ModelSerializer):
    """Membership serializer with user details."""
    
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = ClientMembership
        fields = ['id', 'user', 'role', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']

class ProjectListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for project lists."""
    
    task_count = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = Project
        fields = [
            'id', 'name', 'slug', 'status', 'start_date', 'end_date',
            'task_count', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_task_count(self, obj):
        return obj.tasks.count()

class ProjectDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for project CRUD operations."""
    
    client = ClientSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    task_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = [
            'id', 'client', 'name', 'slug', 'description', 'status',
            'start_date', 'end_date', 'task_count', 'created_by', 'updated_by',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'client', 'created_by', 'updated_by', 'created_at', 'updated_at']
    
    def get_task_count(self, obj):
        return obj.tasks.count()
    
    def validate(self, data):
        """Validate project dates."""
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError("End date must be after start date.")
        
        return data

class ProjectCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating projects."""
    
    class Meta:
        model = Project
        fields = ['name', 'slug', 'description', 'status', 'start_date', 'end_date']
    
    def validate_slug(self, value):
        """Ensure slug is unique within client."""
        client = self.context['client']
        if Project.objects.filter(client=client, slug=value).exists():
            raise serializers.ValidationError("Project with this slug already exists for this client.")
        return value

class TaskListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for task lists."""
    
    assignee_names = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'status', 'priority', 'due_date',
            'assignee_names', 'comment_count', 'is_overdue',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_assignee_names(self, obj):
        return [user.get_full_name() or user.username for user in obj.assignees.all()]
    
    def get_comment_count(self, obj):
        return obj.comments.count()
    
    def get_is_overdue(self, obj):
        return (
            obj.due_date and 
            obj.due_date < timezone.now().date() and 
            obj.status != 'done'
        )

class TaskDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for task CRUD operations."""
    
    project = ProjectListSerializer(read_only=True)
    assignees = UserSerializer(many=True, read_only=True)
    assignee_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False
    )
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    comment_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = [
            'id', 'project', 'title', 'description', 'status', 'priority',
            'due_date', 'assignees', 'assignee_ids', 'comment_count',
            'created_by', 'updated_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'project', 'created_by', 'updated_by', 'created_at', 'updated_at']
    
    def get_comment_count(self, obj):
        return obj.comments.count()
    
    def update(self, instance, validated_data):
        """Handle assignee updates."""
        assignee_ids = validated_data.pop('assignee_ids', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if assignee_ids is not None:
            client = instance.project.client
            valid_users = User.objects.filter(
                id__in=assignee_ids,
                memberships__client=client,
                memberships__is_active=True
            )
            
            if len(valid_users) != len(assignee_ids):
                raise serializers.ValidationError("Some assignees don't have access to this client.")
            
            instance.assignees.set(valid_users)
        
        return instance

class TaskCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating tasks."""
    
    assignee_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True
    )
    
    class Meta:
        model = Task
        fields = ['title', 'description', 'status', 'priority', 'due_date', 'assignee_ids']
    
    def create(self, validated_data):
        """Create task with assignees."""
        assignee_ids = validated_data.pop('assignee_ids', [])
        project = self.context['project']
        
        task = Task.objects.create(project=project, **validated_data)
        
        if assignee_ids:
            client = project.client
            valid_users = User.objects.filter(
                id__in=assignee_ids,
                memberships__client=client,
                memberships__is_active=True
            )
            
            if len(valid_users) != len(assignee_ids):
                raise serializers.ValidationError("Some assignees don't have access to this client.")
            
            task.assignees.set(valid_users)
        
        return task

class CommentSerializer(serializers.ModelSerializer):
    """Comment serializer with author details."""
    
    author = UserSerializer(read_only=True)
    
    class Meta:
        model = Comment
        fields = ['id', 'content', 'author', 'created_at', 'updated_at']
        read_only_fields = ['id', 'author', 'created_at', 'updated_at']

class CommentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating comments."""
    
    class Meta:
        model = Comment
        fields = ['content']
    
    def create(self, validated_data):
        """Create comment with task and author from context."""
        task = self.context['task']
        author = self.context['request'].user
        
        return Comment.objects.create(
            task=task,
            author=author,
            **validated_data
        )
        
class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = "__all__"