from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.db import models

from ms_business_central_api.models.fields import (
    BooleanFalseField,
    CustomDateTimeField,
    CustomJsonField,
    IntegerNullField,
    StringNotNullField,
    StringNullField,
    StringOptionsField,
    TextNotNullField,
)

User = get_user_model()

ONBOARDING_STATE_CHOICES = (
    ('CONNECTION', 'CONNECTION'),
    ('COMPANY_SELECTION', 'COMPANY_SELECTION'),
    ('EXPORT_SETTINGS', 'EXPORT_SETTINGS'),
    ('IMPORT_SETTINGS', 'IMPORT_SETTINGS'),
    ('ADVANCED_CONFIGURATION', 'ADVANCED_CONFIGURATION'),
    ('COMPLETE', 'COMPLETE')
)


def get_default_onboarding_state():
    return 'CONNECTION'


class Workspace(models.Model):
    """
    Workspace model
    """
    id = models.AutoField(primary_key=True)
    name = StringNotNullField(help_text='Name of the workspace')
    user = models.ManyToManyField(User, help_text='Reference to users table')
    org_id = models.CharField(max_length=255, help_text='org id', unique=True)
    reimbursable_last_synced_at = CustomDateTimeField(help_text='Datetime when expenses were pulled last')
    credit_card_last_synced_at = CustomDateTimeField(help_text='Datetime when ccc expenses were pulled last')
    source_synced_at = CustomDateTimeField(help_text='Datetime when source dimensions were pulled')
    destination_synced_at = CustomDateTimeField(help_text='Datetime when destination dimensions were pulled')
    onboarding_state = StringOptionsField(
        max_length=50, choices=ONBOARDING_STATE_CHOICES, default=get_default_onboarding_state,
        help_text='Onboarding status of the workspace'
    )
    ms_business_central_accounts_last_synced_at = CustomDateTimeField(help_text='ms business central accounts last synced at time')
    business_central_company_name = StringNullField(help_text='Business Central Company Name')
    business_central_company_id = StringNullField(help_text='Business Central Company Id')
    created_at = models.DateTimeField(auto_now_add=True, help_text='Created at datetime')
    updated_at = models.DateTimeField(auto_now=True, help_text='Updated at datetime')

    class Meta:
        db_table = 'workspaces'


class BaseModel(models.Model):
    workspace = models.OneToOneField(Workspace, on_delete=models.PROTECT, help_text='Reference to Workspace model')
    created_at = models.DateTimeField(auto_now_add=True, help_text='Created at datetime')
    updated_at = models.DateTimeField(auto_now=True, help_text='Updated at datetime')

    class Meta:
        abstract = True


class BaseForeignWorkspaceModel(models.Model):
    workspace = models.ForeignKey(Workspace, on_delete=models.PROTECT, help_text='Reference to Workspace model')
    created_at = models.DateTimeField(auto_now_add=True, help_text='Created at datetime')
    updated_at = models.DateTimeField(auto_now=True, help_text='Updated at datetime')

    class Meta:
        abstract = True


class FyleCredential(BaseModel):
    """
    Table to store Fyle credentials
    """
    id = models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False)
    refresh_token = TextNotNullField(help_text='Fyle refresh token')
    cluster_domain = StringNullField(help_text='Fyle cluster domain')

    class Meta:
        db_table = 'fyle_credentials'


# Reimbursable Expense Choices
REIMBURSABLE_EXPENSE_EXPORT_TYPE_CHOICES = (
    ('PURCHASE_INVOICE', 'PURCHASE_INVOICE'),
    ('JOURNAL_ENTRY', 'JOURNAL_ENTRY')
)

REIMBURSABLE_EXPENSE_STATE_CHOICES = (
    ('PAYMENT_PROCESSING', 'PAYMENT_PROCESSING'),
    ('PAID', 'PAID')
)

REIMBURSABLE_EXPENSES_GROUPED_BY_CHOICES = (
    ('REPORT', 'report_id'),
    ('EXPENSE', 'expense_id')
)

REIMBURSABLE_EXPENSES_DATE_TYPE_CHOICES = (
    ('LAST_SPENT_AT', 'last_spent_at'),
    ('CURRENT_DATE', 'current_date'),
    ('SPENT_AT', 'spent_at')
)

# Credit Card Expense Choices
CREDIT_CARD_EXPENSE_EXPORT_TYPE_CHOICES = (
    ('JOURNAL_ENTRY', 'JOURNAL_ENTRY'),
)

CREDIT_CARD_EXPENSE_STATE_CHOICES = (
    ('APPROVED', 'APPROVED'),
    ('PAYMENT_PROCESSING', 'PAYMENT_PROCESSING'),
    ('PAID', 'PAID')
)

CREDIT_CARD_EXPENSES_GROUPED_BY_CHOICES = (
    ('REPORT', 'report_id'),
    ('EXPENSE', 'expense_id')
)

CREDIT_CARD_EXPENSES_DATE_TYPE_CHOICES = (
    ('LAST_SPENT_AT', 'last_spent_at'),
    ('POSTED_AT', 'posted_at'),
    ('CREATED_AT', 'created_at')
)

EXPORT_MODE_CHOICES = (
    ('MANUAL', 'MANUAL'),
    ('AUTO', 'AUTO')
)

EMPLOYEE_MAPPING_CHOICES = (
    ('EMPLOYEE', 'EMPLOYEE'),
    ('VENDOR', 'VENDOR')
)

NAME_IN_JOURNAL_ENTRY_CHOICES = (
    ('EMPLOYEE', 'EMPLOYEE'),
    ('MERCHANT', 'MERCHANT')
)


class BusinessCentralCredentials(BaseModel):
    """
    Table to store Business Central credentials
    """

    id = models.AutoField(primary_key=True)
    refresh_token = models.TextField(help_text="Stores Business Central refresh token", null=True)
    is_expired = models.BooleanField(default=False, help_text="Business Central token expiry flag")

    class Meta:
        db_table = "business_central_credentials"

    @staticmethod
    def get_active_business_central(workspace_id):
        return BusinessCentralCredentials.objects.get(
            workspace_id=workspace_id, is_expired=False, refresh_token__isnull=False
        )


class ExportSetting(BaseModel):
    """
    Table to store export settings
    """
    # Reimbursable Expenses Export Settings
    id = models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False)
    reimbursable_expenses_export_type = StringOptionsField(
        choices=REIMBURSABLE_EXPENSE_EXPORT_TYPE_CHOICES,
    )
    default_bank_account_name = StringNullField(help_text='Bank account name')
    default_back_account_id = StringNullField(help_text='Bank Account ID')
    reimbursable_expense_state = StringOptionsField(
        choices=REIMBURSABLE_EXPENSE_STATE_CHOICES
    )
    reimbursable_expense_date = StringOptionsField(
        choices=REIMBURSABLE_EXPENSES_DATE_TYPE_CHOICES
    )
    reimbursable_expense_grouped_by = StringOptionsField(
        choices=REIMBURSABLE_EXPENSES_GROUPED_BY_CHOICES
    )
    # Credit Card Expenses Export Settings
    credit_card_expense_export_type = StringOptionsField(
        choices=CREDIT_CARD_EXPENSE_EXPORT_TYPE_CHOICES
    )
    credit_card_expense_state = StringOptionsField(
        choices=CREDIT_CARD_EXPENSE_STATE_CHOICES
    )
    credit_card_expense_grouped_by = StringOptionsField(
        choices=CREDIT_CARD_EXPENSES_GROUPED_BY_CHOICES
    )
    credit_card_expense_date = StringOptionsField(
        choices=CREDIT_CARD_EXPENSES_DATE_TYPE_CHOICES
    )
    default_vendor_name = StringNullField(help_text='default Vendor Name')
    default_vendor_id = StringNullField(help_text='default Vendor Id')
    journal_entry_folder_id = StringNullField(help_text='default Fyle journal entry id')
    employee_field_mapping = StringOptionsField(
        choices=EMPLOYEE_MAPPING_CHOICES
    )
    name_in_journal_entry = StringOptionsField(
        choices=NAME_IN_JOURNAL_ENTRY_CHOICES
    )
    import_vendors_as_merchants = BooleanFalseField(help_text='toggle for import of vendors as merchant from Business Central')

    class Meta:
        db_table = 'export_settings'


class ImportSetting(BaseModel):
    """
    Table to store Import setting
    """
    id = models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False)
    import_categories = BooleanFalseField(help_text='toggle for import of chart of accounts from Business Central')
    import_vendors_as_merchants = BooleanFalseField(help_text='toggle for import of vendors as merchant from Business Central')
    workspace = models.OneToOneField(Workspace, on_delete=models.PROTECT, help_text='Reference to Workspace model', related_name="import_settings")

    class Meta:
        db_table = 'import_settings'


class AdvancedSetting(BaseModel):
    """
    Table to store advanced setting
    """
    id = models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False)
    expense_memo_structure = ArrayField(
        models.CharField(max_length=255), help_text='Array of fields in memo', null=True
    )
    schedule_is_enabled = BooleanFalseField(help_text='Boolean to check if schedule is enabled')
    start_datetime = CustomDateTimeField(help_text='Schedule start date and time')
    schedule_id = StringNullField(help_text='Schedule id')
    interval_hours = IntegerNullField(help_text='Interval in hours')
    emails_selected = CustomJsonField(help_text='Emails Selected For Email Notification')
    emails_added = CustomJsonField(help_text='Emails Selected For Email Notification')
    auto_create_vendor = BooleanFalseField(help_text='Auto create vendor')

    class Meta:
        db_table = 'advanced_settings'


class LastExportDetail(BaseModel):
    """
    Table to store Last Export Details
    """

    id = models.AutoField(primary_key=True)
    last_exported_at = models.DateTimeField(help_text='Last exported at datetime', null=True)
    export_mode = models.CharField(max_length=50, help_text='Mode of the export Auto / Manual', choices=EXPORT_MODE_CHOICES, null=True)
    total_accounting_exports_count = models.IntegerField(help_text='Total count of accounting exports exported', null=True)
    successful_accounting_exports_count = models.IntegerField(help_text='count of successful accounting_exports ', null=True)
    failed_accounting_exports_count = models.IntegerField(help_text='count of failed accounting_exports ', null=True)

    class Meta:
        db_table = 'last_export_details'
