# Generated by Django 4.1.2 on 2024-06-14 06:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounting_exports', '0002_accountingexport_export_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='error',
            name='repetition_count',
            field=models.IntegerField(default=0, help_text='repetition count for the error'),
        ),
    ]
