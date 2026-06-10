from django.db import migrations, connection


def enable_pgvector(apps, schema_editor):
    # Only run on PostgreSQL — skip SQLite (local dev)
    if connection.vendor == 'postgresql':
        schema_editor.execute("CREATE EXTENSION IF NOT EXISTS vector;")


def disable_pgvector(apps, schema_editor):
    if connection.vendor == 'postgresql':
        schema_editor.execute("DROP EXTENSION IF EXISTS vector;")


class Migration(migrations.Migration):

    initial = False
    dependencies = []
    run_before = [('parser', '0001_initial')]

    operations = [
        migrations.RunPython(
            enable_pgvector,
            reverse_code=disable_pgvector
        )
    ]