from django.db import models

from apps.workspaces.models import BaseForeignWorkspaceModel
from ms_business_central_api.models.fields import (
    CustomDateTimeField,
    CustomJsonField,
    IntegerNotNullField,
    StringNotNullField,
    StringOptionsField,
)

IMPORT_STATUS_CHOICES = (
    ('FATAL', 'FATAL'),
    ('COMPLETE', 'COMPLETE'),
    ('IN_PROGRESS', 'IN_PROGRESS'),
    ('FAILED', 'FAILED')
)


class ImportLog(BaseForeignWorkspaceModel):
    """
    Table to store import logs
    """

    id = models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False)
    attribute_type = StringNotNullField(max_length=150, help_text='Attribute type')
    status = StringOptionsField(help_text='Status', choices=IMPORT_STATUS_CHOICES)
    error_log = CustomJsonField(help_text='Emails Selected For Email Notification')
    total_batches_count = IntegerNotNullField(help_text='Queued batches', default=0)
    processed_batches_count = IntegerNotNullField(help_text='Processed batches', default=0)
    last_successful_run_at = CustomDateTimeField(help_text='Last successful run')

    class Meta:
        db_table = 'import_logs'
        unique_together = ('workspace', 'attribute_type')
