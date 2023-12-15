from django.db import models
from fyle_accounting_mappings.models import CategoryMapping

from apps.accounting_exports.models import AccountingExport
from apps.business_central.exports.base_model import BaseExportModel
from apps.fyle.models import Expense
from apps.workspaces.models import AdvancedSetting
from ms_business_central_api.models.fields import CustomDateTimeField, FloatNullField, StringNullField, TextNotNullField


class JournalEntry(BaseExportModel):
    """
    Journal Entry Model
    """

    accounting_export = models.OneToOneField(AccountingExport, on_delete=models.PROTECT, help_text='Accounting Export reference')
    accounting_date = CustomDateTimeField(help_text='accounting date of purchase invoice')
    amount = FloatNullField(help_text='Total Amount of the journal entry')
    code = StringNullField(max_length=10, help_text='unique code for journal entry')
    description = TextNotNullField(help_text='description for the journal entry')
    invoice_date = CustomDateTimeField(help_text='date of journal entry')
    accounts_payable_account_id = StringNullField(help_text='destination id of accounts payable account')
    location_id = StringNullField(help_text='destination id of location')

    class Meta:
        db_table = 'journal_entries'

    @classmethod
    def create_or_update_object(self, accounting_export: AccountingExport, advance_settings: AdvancedSetting = None):
        """
        Create Purchase Invoice
        :param accounting_export: expense group
        :return: purchase invoices object
        """
        description = accounting_export.description

        vendor_id = self.get_vendor_id(accounting_export=accounting_export)
        amount = self.get_total_amount(accounting_export=accounting_export)
        invoice_date = self.get_invoice_date(accounting_export=accounting_export)

        journal_entry, _ = JournalEntry.objects.update_or_create(
            accounting_export=accounting_export,
            defaults={
                'amount': amount,
                'vendor_id': vendor_id,
                'description': description,
                'invoice_date': invoice_date,
                'workspace_id': accounting_export.workspace_id
            }
        )

        return journal_entry


class JournalEntryLineitems(BaseExportModel):
    """
    Journal Entry Lineitem Model
    """

    accounts_payable_account_id = StringNullField(help_text='destination id of accounts payable account')
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.PROTECT, help_text='Reference to JournalEntry')
    expense = models.OneToOneField(Expense, on_delete=models.PROTECT, help_text='Reference to Expense')
    amount = FloatNullField(help_text='Amount of the invoice')
    description = TextNotNullField(help_text='description for the invoice')
    vendor_id = StringNullField(help_text='destination id of vendor')
    employee_id = StringNullField(help_text='destination id of employee')

    class Meta:
        db_table = 'journal_entry_lineitems'

    @classmethod
    def create_or_update_object(self, accounting_export: AccountingExport, advance_setting: AdvancedSetting):
        """
        Create Purchase Invoice
        :param accounting_export: expense group
        :return: purchase invoices object
        """

        expenses = accounting_export.expenses.all()
        journal_entry = JournalEntry.objects.get(accounting_export=accounting_export)

        journal_entry_lineitem_objects = []

        for lineitem in expenses:
            account = CategoryMapping.objects.filter(
                source_category__value=lineitem.category,
                workspace_id=accounting_export.workspace_id
            ).first()

            description = self.get_expense_purpose(accounting_export.workspace_id, lineitem, lineitem.category, advance_setting)

            journal_entry_lineitem_object, _ = JournalEntryLineitems.objects.update_or_create(
                journal_entry_id=journal_entry.id,
                expense_id=lineitem.id,
                defaults={
                    'amount': lineitem.amount,
                    'accounts_payable_account_id': account.destination_account.destination_id,
                    'description': description,
                    'workspace_id': accounting_export.workspace_id
                }
            )
            journal_entry_lineitem_objects.append(journal_entry_lineitem_object)

        return journal_entry_lineitem_objects
