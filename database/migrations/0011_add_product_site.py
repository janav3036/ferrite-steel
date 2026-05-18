from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('database', '0010_rename_location_to_godown'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='site',
            field=models.CharField(
                blank=True,
                choices=[('site_1', 'Site 1'), ('site_2', 'Site 2')],
                max_length=10,
            ),
        ),
    ]
