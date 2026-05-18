from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quotations', '0013_add_hsn_code_to_line_item'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        "ALTER TABLE quotations_quotationlineitem "
                        "ALTER COLUMN length TYPE VARCHAR(50) "
                        "USING COALESCE(length::text, '');"
                    ),
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[
                migrations.AlterField(
                    model_name='quotationlineitem',
                    name='length',
                    field=models.CharField(blank=True, max_length=50),
                ),
            ],
        ),
    ]
