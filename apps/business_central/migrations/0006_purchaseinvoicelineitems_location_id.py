# Generated by Django 4.1.2 on 2024-01-17 07:39

from django.db import migrations
import ms_business_central_api.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('business_central', '0005_rename_employee_account_id_journalentry_account_id_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchaseinvoicelineitems',
            name='location_id',
            field=ms_business_central_api.models.fields.StringNullField(help_text='location id of the invoice', max_length=255, null=True),
        ),
    ]
