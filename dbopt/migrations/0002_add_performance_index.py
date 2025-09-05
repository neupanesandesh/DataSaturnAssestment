
from django.db import migrations

class Migration(migrations.Migration):
    
    dependencies = [
        ('dbopt', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            "CREATE INDEX project_status_idx ON dbopt_project (status);",
            reverse_sql="DROP INDEX project_status_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX task_status_idx ON dbopt_task (status);",
            reverse_sql="DROP INDEX task_status_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX task_recent_idx ON dbopt_task (created_at DESC);",
            reverse_sql="DROP INDEX task_recent_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX project_date_idx ON dbopt_project (created_at);",
            reverse_sql="DROP INDEX project_date_idx;"
        ),
        
        migrations.RunSQL(
            "CREATE INDEX project_client_idx ON dbopt_project (client_id);",
            reverse_sql="DROP INDEX project_client_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX task_project_idx ON dbopt_task (project_id);",
            reverse_sql="DROP INDEX task_project_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX task_assignee_idx ON dbopt_task (assignee_id);",
            reverse_sql="DROP INDEX task_assignee_idx;"
        ),
        
        migrations.RunSQL(
            "CREATE INDEX client_active_projects_idx ON dbopt_project (client_id, status);",
            reverse_sql="DROP INDEX client_active_projects_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX project_task_counts_idx ON dbopt_task (project_id, status);",
            reverse_sql="DROP INDEX project_task_counts_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX user_task_stats_idx ON dbopt_task (assignee_id, status);",
            reverse_sql="DROP INDEX user_task_stats_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX recent_project_tasks_idx ON dbopt_task (project_id, created_at DESC);",
            reverse_sql="DROP INDEX recent_project_tasks_idx;"
        ),
    ]