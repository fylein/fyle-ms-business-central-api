# Generated by Django 4.1.2 on 2024-12-11 10:37

from django.db import migrations
import ms_business_central_api.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('workspaces', '0004_importsetting_charts_of_accounts'),
    ]

    operations = [
        migrations.AddField(
            model_name='exportsetting',
            name='default_CCC_bank_account_id',
            field=ms_business_central_api.models.fields.StringNullField(help_text='CCC Bank Account ID', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='exportsetting',
            name='default_CCC_bank_account_name',
            field=ms_business_central_api.models.fields.StringNullField(help_text='CCC Bank account name', max_length=255, null=True),
        ),
    ]
