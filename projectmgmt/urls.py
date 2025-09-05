
from rest_framework_nested import routers
from .views import ClientViewSet, ProjectViewSet, TaskViewSet, CommentViewSet

router = routers.SimpleRouter()
router.register(r'clients', ClientViewSet, basename='clients')

# Projects nested under clients
clients_router = routers.NestedSimpleRouter(router, r'clients', lookup='client')
clients_router.register(r'projects', ProjectViewSet, basename='client-projects')

# Tasks nested under projects
projects_router = routers.NestedSimpleRouter(clients_router, r'projects', lookup='project')
projects_router.register(r'tasks', TaskViewSet, basename='project-tasks')

# Comments nested under tasks
tasks_router = routers.NestedSimpleRouter(projects_router, r'tasks', lookup='task')
tasks_router.register(r'comments', CommentViewSet, basename='task-comments')

urlpatterns = router.urls + clients_router.urls + projects_router.urls + tasks_router.urls
