from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('database', '0014_product_base_product_product_rate_offset'),
    ]

    operations = [
        # Rename existing make (Main/Rolling/Plate) to category
        migrations.RenameField(
            model_name='product',
            old_name='make',
            new_name='category',
        ),
        # Update choices on category field
        migrations.AlterField(
            model_name='product',
            name='category',
            field=models.CharField(
                max_length=10,
                choices=[('main', 'Main'), ('rolling', 'Rolling'), ('plate', 'Plate')],
            ),
        ),
        # Add new make field (manufacturer)
        migrations.AddField(
            model_name='product',
            name='make',
            field=models.CharField(
                max_length=30,
                blank=True,
                choices=[
                    ('Jindal', 'Jindal'), ('Sail', 'Sail'), ('JSPL', 'JSPL'),
                    ('TATA', 'TATA'), ('Posco', 'Posco'), ('RINL', 'RINL'),
                    ('Rolling Apollo', 'Rolling Apollo'), ('Khanna', 'Khanna'),
                    ('Essar / AMNS', 'Essar / AMNS'), ('Essar', 'Essar'),
                    ('Goel', 'Goel'), ('VSP / SAIL', 'VSP / SAIL'),
                    ('Sail / Jindal', 'Sail / Jindal'), ('Others', 'Others'),
                ],
                default='',
            ),
            preserve_default=False,
        ),
    ]
