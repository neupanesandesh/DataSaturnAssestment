from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied

class MultiTenantPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """
        Check if the user belongs to the client related to this object.
        """
        attr = getattr(view, 'permission_object_attr', None)
        if not attr:
            return True

        target_obj = getattr(obj, attr, None)
        if target_obj is None:
            raise PermissionDenied(f"Cannot find '{attr}' on object for permission check.")

        client = None
        if attr == 'client':
            client = target_obj
        elif attr == 'project':
            client = target_obj.client
        elif attr == 'task':
            client = target_obj.project.client
        else:
            raise PermissionDenied("Invalid permission_object_attr specified.")

        if not client.users.filter(id=request.user.id).exists():
            raise PermissionDenied("You do not have access to this client.")

        return True