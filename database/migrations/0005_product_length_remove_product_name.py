from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('database', '0004_product_sub_type'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='product_name',
        ),
        migrations.AddField(
            model_name='product',
            name='length',
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=8, null=True),
        ),
    ]
