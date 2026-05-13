from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('database', '0005_product_length_remove_product_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='length',
            field=models.CharField(blank=True, max_length=50),
        ),
    ]
