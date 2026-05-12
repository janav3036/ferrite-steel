from django.db import migrations


def rename_india_mart(apps, schema_editor):
    User = apps.get_model('aegis', 'CustomUser')
    User.objects.filter(team='india_mart').update(team='team_9')


def reverse_rename(apps, schema_editor):
    User = apps.get_model('aegis', 'CustomUser')
    User.objects.filter(team='team_9').update(team='india_mart')


class Migration(migrations.Migration):

    dependencies = [
        ('aegis', '0002_customuser_team_alter_customuser_role'),
    ]

    operations = [
        migrations.RunPython(rename_india_mart, reverse_rename),
    ]
