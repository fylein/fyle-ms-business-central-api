# Generated by Django 4.2.18 on 2025-02-28 07:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workspaces', '0006_rename_default_ccc_bank_account_id_exportsetting_default_ccc_bank_account_id_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='businesscentralcredentials',
            name='environment',
            field=models.CharField(default='production', help_text='Business Central Environment', max_length=255),
        ),
    ]
