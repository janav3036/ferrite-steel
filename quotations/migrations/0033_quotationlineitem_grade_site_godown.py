# Generated manually — make/length become real choice fields, add grade/site/godown

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quotations', '0032_alter_quotationlineitem_uom'),
    ]

    operations = [
        migrations.AlterField(
            model_name='quotationlineitem',
            name='make',
            field=models.CharField(blank=True, max_length=100, choices=[('Jindal', 'Jindal'), ('Sail', 'Sail'), ('JSPL', 'JSPL'), ('TATA', 'TATA'), ('Posco', 'Posco'), ('RINL', 'RINL'), ('Rolling', 'Rolling'), ('Apollo', 'Apollo'), ('Khanna', 'Khanna'), ('Essar / AMNS', 'Essar / AMNS'), ('Essar', 'Essar'), ('Goel', 'Goel'), ('VSP / SAIL', 'VSP / SAIL'), ('Sail / Jindal', 'Sail / Jindal'), ('Others', 'Others')]),
        ),
        migrations.AlterField(
            model_name='quotationlineitem',
            name='length',
            field=models.CharField(blank=True, max_length=50, choices=[('6MTR', '6MTR'), ('12MTR', '12MTR'), ('5-6MTR', '5-6MTR'), ('10-12MTR', '10-12MTR'), ('7-12 MTR', '7-12 MTR'), ('2.5MTR', '2.5MTR'), ('8 feet', '8 feet'), ('10 feet', '10 feet'), ('12 feet', '12 feet'), ('14 feet', '14 feet'), ('16 feet', '16 feet'), ('18 feet', '18 feet'), ('20 feet', '20 feet'), ('2500', '2500'), ('3000', '3000'), ('3150', '3150'), ('5000', '5000'), ('6000', '6000'), ('6300', '6300'), ('8000', '8000'), ('10000', '10000'), ('12000', '12000'), ('CUTSIZE', 'CUTSIZE'), ('Random', 'Random'), ('Other', 'Other')]),
        ),
        migrations.AddField(
            model_name='quotationlineitem',
            name='grade',
            field=models.CharField(blank=True, max_length=50, choices=[('E250', 'E250'), ('E250BR', 'E250BR'), ('E250B0', 'E250B0'), ('E350BR', 'E350BR'), ('E350C', 'E350C'), ('516-GR 60', '516-GR 60'), ('516-GR 70', '516-GR 70'), ('C45', 'C45'), ('513D', '513D'), ('DD', 'DD'), ('FE500', 'FE500'), ('FE500D', 'FE500D'), ('HCRM', 'HCRM'), ('CRS', 'CRS'), ('1018', '1018'), ('EN8', 'EN8'), ('EN9', 'EN9'), ('AZ 70', 'AZ 70'), ('AZ 150', 'AZ 150'), ('AZ 150 C+', 'AZ 150 C+'), ('PPGI', 'PPGI'), ('PPGL', 'PPGL'), ('SHS', 'SHS'), ('IS4923', 'IS4923'), ('IS1161', 'IS1161'), ('SS 304', 'SS 304'), ('SS316', 'SS316')]),
        ),
        migrations.AddField(
            model_name='quotationlineitem',
            name='site',
            field=models.CharField(blank=True, max_length=10, choices=[('site_1', 'Site 1'), ('site_2', 'Site 2')]),
        ),
        migrations.AddField(
            model_name='quotationlineitem',
            name='godown',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
