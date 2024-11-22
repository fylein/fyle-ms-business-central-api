# Generated by Django 4.1.2 on 2024-11-15 12:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('business_central', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='journalentrylineitems',
            name='dimensions',
            field=models.JSONField(help_text='Business Central dimensions', null=True),
        ),
        migrations.AddField(
            model_name='purchaseinvoicelineitems',
            name='dimensions',
            field=models.JSONField(help_text='Business Central dimensions', null=True),
        ),
    ]