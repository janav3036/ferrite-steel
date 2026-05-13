from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('database', '0006_alter_product_length'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='sub_type',
            field=models.CharField(
                blank=True,
                choices=[
                    ('angle', 'Angle'),
                    ('channel', 'Channel'),
                    ('ub', 'UB'),
                    ('uc', 'UC'),
                    ('beam', 'Beam'),
                    ('flat', 'Flat'),
                    ('red_material', 'Red Material'),
                    ('tmt', 'TMT'),
                ],
                max_length=20,
            ),
        ),
    ]
