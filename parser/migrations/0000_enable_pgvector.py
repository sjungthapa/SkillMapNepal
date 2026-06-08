from django.db import migrations


class Migration(migrations.Migration):

    initial = False
    dependencies = []
    run_before = [('parser', '0001_initial')]

    operations = [
        migrations.RunSQL(
            sql="CREATE EXTENSION IF NOT EXISTS vector;",
            reverse_sql="DROP EXTENSION IF EXISTS vector;"
        )
    ]