# projectmgmt/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Client, ClientMembership, Project, Task, Comment


class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('email', 'username', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('username', 'first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2'),
        }),
    )
    search_fields = ('email', 'username')
    ordering = ('email',)

# Registering all models
admin.site.register(User, CustomUserAdmin)
admin.site.register(Client)
admin.site.register(ClientMembership)
admin.site.register(Project)
admin.site.register(Task)
admin.site.register(Comment)