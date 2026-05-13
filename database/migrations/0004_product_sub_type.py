from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('database', '0003_customer_handling_team'),
    ]

    operations = [
        migrations.AddField(
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
                ],
                max_length=10,
            ),
        ),
    ]
