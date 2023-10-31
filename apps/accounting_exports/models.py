from django.db import models
from django.contrib.postgres.fields import ArrayField

from ms_business_central_api.models.fields import (
    StringNotNullField,
    StringNullField,
    CustomJsonField,
    CustomDateTimeField,
    StringOptionsField,
    IntegerNullField
)
from apps.workspaces.models import BaseForeignWorkspaceModel, BaseModel
from apps.fyle.models import Expense

TYPE_CHOICES = (
    ('INVOICES', 'INVOICES'),
    ('DIRECT_COST', 'DIRECT_COST'),
    ('FETCHING_REIMBURSABLE_EXPENSES', 'FETCHING_REIMBURSABLE_EXPENSES'),
    ('FETCHING_CREDIT_CARD_EXPENENSES', 'FETCHING_CREDIT_CARD_EXPENENSES')
)

ERROR_TYPE_CHOICES = (('EMPLOYEE_MAPPING', 'EMPLOYEE_MAPPING'), ('CATEGORY_MAPPING', 'CATEGORY_MAPPING'), ('SAGE300_ERROR', 'SAGE300_ERROR'))

EXPORT_MODE_CHOICES = (
    ('MANUAL', 'MANUAL'),
    ('AUTO', 'AUTO')
)


class AccountingExport(BaseForeignWorkspaceModel):
    """
    Table to store accounting exports
    """
    id = models.AutoField(primary_key=True)
    type = StringOptionsField(choices=TYPE_CHOICES, help_text='Task type')
    fund_source = StringNotNullField(help_text='Expense fund source')
    mapping_errors = ArrayField(help_text='Mapping errors', base_field=models.CharField(max_length=255), blank=True, null=True)
    expenses = models.ManyToManyField(Expense, help_text="Expenses under this Expense Group")
    task_id = StringNullField(help_text='Fyle Jobs task reference')
    description = CustomJsonField(help_text='Description')
    status = StringNotNullField(help_text='Task Status')
    detail = CustomJsonField(help_text='Task Response')
    sage_300_errors = CustomJsonField(help_text='Sage 300 Errors')
    exported_at = CustomDateTimeField(help_text='time of export')

    class Meta:
        db_table = 'accounting_exports'


class AccountingExportSummary(BaseModel):
    """
    Table to store accounting export summary
    """
    id = models.AutoField(primary_key=True)
    last_exported_at = CustomDateTimeField(help_text='Last exported at datetime')
    next_export_at = CustomDateTimeField(help_text='next export datetime')
    export_mode = StringOptionsField(choices=EXPORT_MODE_CHOICES, help_text='Export mode')
    total_accounting_export_count = IntegerNullField(help_text='Total count of accounting export exported')
    successful_accounting_export_count = IntegerNullField(help_text='count of successful accounting export')
    failed_accounting_export_count = IntegerNullField(help_text='count of failed accounting export')

    class Meta:
        db_table = 'accounting_export_summary'
