from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('database', '0021_merge_20260802_0000'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='category',
            field=models.CharField(blank=True, max_length=10, choices=[('main', 'Main'), ('rolling', 'Rolling'), ('jindal', 'Jindal'), ('others', 'Others')]),
        ),
    ]
