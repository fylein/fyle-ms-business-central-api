from django.db import models
from fyle_accounting_mappings.models import CategoryMapping

from apps.accounting_exports.models import AccountingExport
from apps.business_central.exports.base_model import BaseExportModel
from apps.fyle.models import Expense
from apps.workspaces.models import AdvancedSetting, ExportSetting
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
    amount = FloatNullField(help_text='Amount of the invoice')
    comment = TextNotNullField(help_text='description for the invoice')
    description = TextNullField(help_text='description for the invoice')
    invoice_date = CustomDateTimeField(help_text='date of invoice')
    document_number = TextNotNullField(help_text='document number of the invoice')
    accounting_export = models.OneToOneField(AccountingExport, on_delete=models.PROTECT, help_text='Accounting Export reference', related_name='journal_entry')

    class Meta:
        db_table = 'journal_entries'

    @classmethod
    def create_or_update_object(self, accounting_export: AccountingExport, advance_setting: AdvancedSetting, export_settings: ExportSetting):
        """
        Create Jornal Entry object
        :param accounting_export: expense group
        :return: purchase invoices object
        """
        expenses = accounting_export.expenses.all()

        account_id = export_settings.default_back_account_id

        comment = "Consolidated Debit Entry For Report {}".format(accounting_export.description['claim_number'] if accounting_export.description and accounting_export.description['claim_number'] else accounting_export.description['expense_number'])

        invoice_date = self.get_invoice_date(accounting_export=accounting_export)

        journal_entry_object, _ = JournalEntry.objects.update_or_create(
            accounting_export= accounting_export,
            defaults={
                'amount': sum([expense.amount for expense in expenses]) * -1,
                'document_number': accounting_export.description['claim_number'] if accounting_export.description and accounting_export.description['claim_number'] else accounting_export.description['expense_number'],
                'accounts_payable_account_id': account_id,
                'comment': comment,
                'workspace_id': accounting_export.workspace_id,
                'invoice_date': invoice_date
            }
        )

        return journal_entry_object


class JournalEntryLineItems(BaseExportModel):
    """
    Journal Entry Model
    """

    accounts_payable_account_id = StringNullField(help_text='destination id of accounts payable account')
    expense = models.OneToOneField(Expense, on_delete=models.PROTECT, help_text='Reference to Expense')
    amount = FloatNullField(help_text='Amount of the invoice')
    comment = TextNotNullField(help_text='description for the invoice')
    description = TextNullField(help_text='description for the invoice')
    invoice_date = CustomDateTimeField(help_text='date of invoice')
    document_number = TextNotNullField(help_text='document number of the invoice')
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.PROTECT, help_text='Journal Entry reference', related_name='journal_entry_lineitems')

    class Meta:
        db_table = 'journal_entries_lineitems'

    @classmethod
    def create_or_update_object(self, accounting_export: AccountingExport, advance_setting: AdvancedSetting):
        """
        Create Jornal Entry LineItems object
        :param accounting_export: expense group
        :return: purchase invoices object
        """
        expenses = accounting_export.expenses.all()
        journal_entry = JournalEntry.objects.get(accounting_export=accounting_export)

        journal_entry_lineitems = []

        for lineitem in expenses:
            account = CategoryMapping.objects.filter(
                source_category__value=lineitem.category,
                workspace_id=accounting_export.workspace_id
            ).first()

            comment = self.get_expense_comment(accounting_export.workspace_id, lineitem, lineitem.category, advance_setting)

            invoice_date = self.get_invoice_date(accounting_export=accounting_export)

            journal_entry_lineitems_object, _ = JournalEntryLineItems.objects.update_or_create(
                journal_entry_id = journal_entry.id,
                expense_id=lineitem.id,
                defaults={
                    'amount': lineitem.amount,
                    'document_number':  accounting_export.description['claim_number'] if accounting_export.description and accounting_export.description['claim_number'] else accounting_export.description['expense_number'],
                    'accounts_payable_account_id': account.destination_account.destination_id,
                    'comment': comment,
                    'workspace_id': accounting_export.workspace_id,
                    'invoice_date': invoice_date,
                    'description': lineitem.purpose if lineitem.purpose else None
                }
            )
            journal_entry_lineitems.append(journal_entry_lineitems_object)

        return journal_entry_lineitems
