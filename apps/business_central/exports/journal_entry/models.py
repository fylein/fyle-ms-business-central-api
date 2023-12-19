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

    accounts_payable_account_id = StringNullField(help_text='destination id of accounts payable account')
    expense = models.OneToOneField(Expense, on_delete=models.PROTECT, help_text='Reference to Expense')
    amount = FloatNullField(help_text='Amount of the invoice')
    description = TextNotNullField(help_text='description for the invoice')
    vendor_id = StringNullField(help_text='destination id of vendor')
    employee_id = StringNullField(help_text='destination id of employee')
    invoice_date = CustomDateTimeField(help_text='date of invoice')

    class Meta:
        db_table = 'journal_entries'

    @classmethod
    def create_or_update_object(self, accounting_export: AccountingExport, advance_setting: AdvancedSetting):
        """
        Create Jornal Entry object
        :param accounting_export: expense group
        :return: purchase invoices object
        """

        expenses = accounting_export.expenses.all()
        vendor_id = None
        employee_id = None

        journal_entry_objects = []

        for lineitem in expenses:
            account = CategoryMapping.objects.filter(
                source_category__value=lineitem.category,
                workspace_id=accounting_export.workspace_id
            ).first()

            # vendor_id = self.get_vendor_id(accounting_export.workspace_id, lineitem.vendor, advance_setting)
            # employee_id = self.get_employee_id(accounting_export.workspace_id, lineitem.employee_email, advance_setting)

            #description = self.get_expense_purpose(accounting_export.workspace_id, lineitem, lineitem.category, advance_setting)

            invoice_date = self.get_invoice_date(accounting_export=accounting_export)

            journal_entry_object, _ = JournalEntry.objects.update_or_create(
                expense_id=lineitem.id,
                defaults={
                    'amount': lineitem.amount,
                    'accounts_payable_account_id': account.destination_account.destination_id,
                    'description': " testing desc rushi",
                    'workspace_id': accounting_export.workspace_id,
                    'vendor_id': vendor_id,
                    'employee_id': employee_id,
                    'invoice_date': invoice_date
                }
            )
            journal_entry_objects.append(journal_entry_object)

        return journal_entry_objects
