# Generated manually — flat item-based Product catalog redesign

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('database', '0018_alter_product_sub_type'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='make',
        ),
        migrations.RemoveField(
            model_name='product',
            name='sub_type',
        ),
        migrations.RemoveField(
            model_name='product',
            name='length',
        ),
        migrations.RemoveField(
            model_name='product',
            name='grade',
        ),
        migrations.RemoveField(
            model_name='product',
            name='pieces',
        ),
        migrations.RemoveField(
            model_name='product',
            name='godown',
        ),
        migrations.RemoveField(
            model_name='product',
            name='site',
        ),
        migrations.RemoveField(
            model_name='product',
            name='size',
        ),
        migrations.AddField(
            model_name='product',
            name='item_no',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='product',
            name='product_name',
            field=models.CharField(default='', max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='product',
            name='unit',
            field=models.CharField(choices=[('ton', 'Ton'), ('kg', 'Kg'), ('mtr', 'Mtr'), ('nos', 'Nos')], default='ton', max_length=3),
        ),
        migrations.AlterField(
            model_name='product',
            name='category',
            field=models.CharField(blank=True, choices=[('main', 'Main'), ('rolling', 'Rolling'), ('jindal', 'Jindal')], max_length=10),
        ),
        migrations.AlterModelOptions(
            name='product',
            options={'ordering': ['category', 'item_no'], 'verbose_name': 'Product', 'verbose_name_plural': 'Products'},
        ),
    ]
