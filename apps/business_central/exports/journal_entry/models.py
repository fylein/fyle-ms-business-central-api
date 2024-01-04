from django.db import models
from fyle_accounting_mappings.models import CategoryMapping

from apps.accounting_exports.models import AccountingExport
from apps.business_central.exports.base_model import BaseExportModel
from apps.fyle.models import Expense
from apps.workspaces.models import AdvancedSetting
from ms_business_central_api.models.fields import (
    CustomDateTimeField,
    FloatNullField,
    StringNullField,
    TextNotNullField,
    TextNullField,
)


class JournalEntry(BaseExportModel):
    """
    Journal Entry Model
    """

    accounts_payable_account_id = StringNullField(help_text='destination id of accounts payable account')
    expense = models.OneToOneField(Expense, on_delete=models.PROTECT, help_text='Reference to Expense')
    amount = FloatNullField(help_text='Amount of the invoice')
    comment = TextNotNullField(help_text='description for the invoice')
    description = TextNullField(help_text='description for the invoice')
    invoice_date = CustomDateTimeField(help_text='date of invoice')
    accounting_export = models.OneToOneField(AccountingExport, on_delete=models.PROTECT, help_text='Accounting Export reference')

    class Meta:
        db_table = 'journal_entries'

    @classmethod
    def create_or_update_object(self, accounting_export: AccountingExport, advance_setting: AdvancedSetting):
        """
        Create Jornal Entry object
        :param accounting_export: expense group
        :return: purchase invoices object
        """
        expense = accounting_export.expenses.first()

        account = CategoryMapping.objects.filter(
            source_category__value=expense.category,
            workspace_id=accounting_export.workspace_id
        ).first()

        comment = self.get_expense_comment(accounting_export.workspace_id, expense, expense.category, advance_setting)

        invoice_date = self.get_invoice_date(accounting_export=accounting_export)

        journal_entry_object, _ = JournalEntry.objects.update_or_create(
            expense_id=expense.id,
            defaults={
                'amount': expense.amount,
                'accounts_payable_account_id': account.destination_account.destination_id,
                'comment': comment,
                'workspace_id': accounting_export.workspace_id,
                'invoice_date': invoice_date,
                'accounting_export_id': accounting_export.id,
                'description': expense.purpose if expense.purpose else None
            }
        )

        return journal_entry_object
