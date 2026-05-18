from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('database', '0008_alter_product_options_alter_product_hsn_code'),
    ]

    operations = [
        migrations.RenameField(
            model_name='product',
            old_name='type',
            new_name='make',
        ),
    ]
