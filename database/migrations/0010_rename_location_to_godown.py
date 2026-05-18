from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('database', '0009_rename_type_to_make'),
    ]

    operations = [
        migrations.RenameField(
            model_name='product',
            old_name='location',
            new_name='godown',
        ),
    ]
