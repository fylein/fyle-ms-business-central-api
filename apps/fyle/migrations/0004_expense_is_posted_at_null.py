# Generated by Django 4.1.2 on 2024-11-22 10:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fyle', '0003_remove_expense_settlement_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='expense',
            name='is_posted_at_null',
            field=models.BooleanField(default=False, help_text='Flag check if posted at is null or not'),
        ),
    ]
