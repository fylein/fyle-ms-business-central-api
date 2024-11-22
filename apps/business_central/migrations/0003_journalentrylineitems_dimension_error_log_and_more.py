# Generated by Django 4.1.2 on 2024-11-18 08:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('business_central', '0002_journalentrylineitems_dimensions_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='journalentrylineitems',
            name='dimension_error_log',
            field=models.JSONField(help_text='dimension set response log', null=True),
        ),
        migrations.AddField(
            model_name='purchaseinvoicelineitems',
            name='dimension_error_log',
            field=models.JSONField(help_text='dimension set response log', null=True),
        ),
    ]