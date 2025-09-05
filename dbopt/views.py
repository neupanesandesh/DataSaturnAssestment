
from django.db.models import Count, Case, When, FloatField, Q,Value, Cast
from .performance_monitoring import monitor_queries
from rest_framework.views import APIView
from django.db.models.functions import Concat
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from .models import Client, User, Project, Task
from django.core.cache import cache

# views.py - This view has multiple performance issues
class OptimizedProjectDashboardView(APIView):
    @monitor_queries
    def get_cache_key(self, client_id):
        """Generate cache key for dashboard data"""
        return f"dashboard_client_{client_id}"
    
    def get(self, request, client_id):
        cache_key = self.get_cache_key(client_id)
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)
        
        client = get_object_or_404(Client, id=client_id)
        
        projects = Project.objects.select_related('client').filter(client=client)
        
        dashboard_data = {
            'client_name': client.name,
            'total_projects': projects.count(),
            'active_projects': [],
            'recent_tasks': [],
            'team_stats': {}
        }
        
        active_projects = projects.filter(status='active').annotate(
            total_tasks=Count('task'),
            completed_tasks=Count('task_set', filter=Q(task__status='completed'))
        ).values('id', 'name', 'total_tasks', 'completed_tasks')
        
        dashboard_data['active_projects'] = [
            {
                'id': project['id'],
                'name': project['name'],
                'total_tasks': project['total_tasks'],
                'completed_tasks': project['completed_tasks'],
                'progress': round((project['completed_tasks'] / project['total_tasks'] * 100), 2) 
                           if project['total_tasks'] > 0 else 0
            } for project in active_projects
        ]
        
        # Get recent tasks across all projects
        # all_tasks = []
        # for project in projects:
        #     project_tasks = Task.objects.filter(project=project).order_by('-created_at')
        #     for task in project_tasks:
        #         task.project_name = project.name
        #         task.assignee_name = task.assignee.first_name + ' ' + task.assignee.last_name if task.assignee else 'Unassigned'
        #         all_tasks.append(task)
        
        
        #--------------------------------------------------------------------------------new implementation------------------------------------------------------
        recent_tasks = Task.objects.select_related('project', 'assignee').filter(
            project__client=client
        ).annotate(
            project_name=Value('project__name'),
            assignee_name=Case(
                When(assignee__isnull=True, then=Value('Unassigned')),
                default=Concat('assignee__first_name', Value(' '), 'assignee__last_name')
            )
        ).order_by('-created_at')[:10]
        
        dashboard_data['recent_tasks'] = [
            {
                'id': task.id,
                'title': task.title,
                'project_name': task.project.name,
                'assignee_name': task.assignee_name if hasattr(task, 'assignee_name') else 
                                (f"{task.assignee.first_name} {task.assignee.last_name}" if task.assignee else 'Unassigned'),
                'created_at': task.created_at
            } for task in recent_tasks
        ]     
           
        #------------------------------------------------------------------------old implementation with issues -------------------------------------------------------   
        # Sort and get recent 10
        # all_tasks.sort(key=lambda x: x.created_at, reverse=True)
        # dashboard_data['recent_tasks'] = [
        #     {
        #         'id': task.id,
        #         'title': task.title,
        #         'project_name': task.project_name,
        #         'assignee_name': task.assignee_name,
        #         'created_at': task.created_at
        #     } for task in all_tasks[:10]
        # ]
        
        # Team statistics
        # team_members = User.objects.filter(clients=client)
        # for member in team_members:
        #     member_tasks = Task.objects.filter(assignee=member, project_client=client)
        #     dashboard_data['team_stats'][member.id] = {
        #         'name': member.first_name + ' ' + member.last_name,
        #         'total_tasks': member_tasks.count(),
        #         'completed_tasks': member_tasks.filter(status='completed').count(),
        #         'pending_tasks': member_tasks.filter(status='pending').count()
        #     }
        
        # return Response(dashboard_data)
        
        #Team stats new implementation
        
        # team_members = User.objects.filter(clients=client).annotate(
        #     full_name=Concat('first_name', Value(' '), 'last_name')
        # )
        
        
        #-------------------------------------------------------------------------------new implementation------------------------------------------------------
        team_members_with_stats = User.objects.filter(clients=client).annotate(
            total_tasks=Count('task_set', filter=Q(task__project__client=client)),
            completed_tasks=Count('task_set', filter=Q(task__project__client=client, task__status='completed')),
            pending_tasks=Count('task_set', filter=Q(task__project__client=client, task__status='pending')),
            full_name=Concat('first_name', Value(' '), 'last_name')
        ).values('id', 'full_name', 'total_tasks', 'completed_tasks', 'pending_tasks')
        

        for member in team_members_with_stats:
            dashboard_data['team_stats'][member['id']] = {
                'name': member['full_name'],
                'total_tasks': member['total_tasks'],
                'completed_tasks': member['completed_tasks'],
                'pending_tasks': member['pending_tasks']
            }
        
        cache.set(cache_key, dashboard_data, 600)  # Cache for 5 minutes
        
        return Response(dashboard_data)