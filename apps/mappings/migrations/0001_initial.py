# Generated by Django 4.1.2 on 2023-12-19 06:51

from django.db import migrations, models
import django.db.models.deletion
import ms_business_central_api.models.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('workspaces', '0002_alter_workspace_ms_business_central_accounts_last_synced_at_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ImportLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Created at datetime')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Updated at datetime')),
                ('attribute_type', ms_business_central_api.models.fields.StringNotNullField(help_text='Attribute type', max_length=150)),
                ('status', ms_business_central_api.models.fields.StringOptionsField(choices=[('FATAL', 'FATAL'), ('COMPLETE', 'COMPLETE'), ('IN_PROGRESS', 'IN_PROGRESS'), ('FAILED', 'FAILED')], default='', help_text='Status', max_length=255, null=True)),
                ('error_log', ms_business_central_api.models.fields.CustomJsonField(default=list, help_text='Emails Selected For Email Notification', null=True)),
                ('total_batches_count', ms_business_central_api.models.fields.IntegerNotNullField(default=0, help_text='Queued batches')),
                ('processed_batches_count', ms_business_central_api.models.fields.IntegerNotNullField(default=0, help_text='Processed batches')),
                ('last_successful_run_at', ms_business_central_api.models.fields.CustomDateTimeField(help_text='Last successful run', null=True)),
                ('workspace', models.ForeignKey(help_text='Reference to Workspace model', on_delete=django.db.models.deletion.PROTECT, to='workspaces.workspace')),
            ],
            options={
                'db_table': 'import_logs',
                'unique_together': {('workspace', 'attribute_type')},
            },
        ),
    ]
