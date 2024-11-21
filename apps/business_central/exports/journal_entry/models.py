from django.db import models
from django.db.models import JSONField

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
    account_id = StringNullField(help_text='destination id of employee account')
    account_type = StringNullField(help_text='destination id of employee account')
    amount = FloatNullField(help_text='Amount of the invoice')
    comment = TextNotNullField(help_text='description for the invoice')
    description = TextNullField(help_text='description for the invoice')
    invoice_date = CustomDateTimeField(help_text='date of invoice')
    document_number = TextNotNullField(help_text='document number of the invoice')
    accounting_export = models.OneToOneField(AccountingExport, on_delete=models.PROTECT, help_text='Accounting Export reference', related_name='journal_entry')

    class Meta:
        db_table = 'journal_entries'

    @classmethod
    def create_or_update_object(self, accounting_export: AccountingExport, _: AdvancedSetting, export_settings: ExportSetting):
        """
        Create Jornal Entry object
        :param accounting_export: expense group
        :return: purchase invoices object
        """
        expenses = accounting_export.expenses.all()

        accounts_payable_account_id = export_settings.default_bank_account_id

        document_number = accounting_export.description['claim_number'] if accounting_export.description and accounting_export.description.get('claim_number') else accounting_export.description['expense_number']

        comment = "Consolidated Credit Entry For Report/Expense {}".format(document_number)

        invoice_date = self.get_invoice_date(accounting_export=accounting_export)

        account_type, account_id = self.get_account_id_type(accounting_export=accounting_export, export_settings=export_settings)

        journal_entry_object, _ = JournalEntry.objects.update_or_create(
            accounting_export= accounting_export,
            defaults={
                'amount': sum([expense.amount for expense in expenses]),
                'document_number': document_number,
                'accounts_payable_account_id': accounts_payable_account_id,
                'account_id': account_id,
                'account_type': account_type,
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
    account_id = StringNullField(help_text='destination id of employee account')
    account_type = StringNullField(help_text='destination id of employee account')
    expense = models.OneToOneField(Expense, on_delete=models.PROTECT, help_text='Reference to Expense')
    amount = FloatNullField(help_text='Amount of the invoice')
    comment = TextNotNullField(help_text='description for the invoice')
    description = TextNullField(help_text='description for the invoice')
    invoice_date = CustomDateTimeField(help_text='date of invoice')
    document_number = TextNotNullField(help_text='document number of the invoice')
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.PROTECT, help_text='Journal Entry reference', related_name='journal_entry_lineitems')
    dimensions = JSONField(default=list, help_text='Business Central dimensions')
    dimension_error_log = JSONField(null=True, help_text='dimension set response log')
    dimension_success_log = JSONField(null=True, help_text='dimension set success response log')

    class Meta:
        db_table = 'journal_entries_lineitems'

    @classmethod
    def create_or_update_object(self, accounting_export: AccountingExport, advance_setting: AdvancedSetting, export_settings: ExportSetting):
        """
        Create Jornal Entry LineItems object
        :param accounting_export: expense group
        :return: purchase invoices object
        """
        expenses = accounting_export.expenses.all()
        journal_entry = JournalEntry.objects.get(accounting_export=accounting_export)

        journal_entry_lineitems = []

        for lineitem in expenses:
            category = lineitem.category if (lineitem.category == lineitem.sub_category or lineitem.sub_category == None) else '{0} / {1}'.format(lineitem.category, lineitem.sub_category)

            account = CategoryMapping.objects.filter(
                source_category__value=category,
                workspace_id=accounting_export.workspace_id
            ).first()

            comment = self.get_expense_comment(accounting_export.workspace_id, lineitem, lineitem.category, advance_setting)

            invoice_date = self.get_invoice_date(accounting_export=accounting_export)

            account_type, account_id = self.get_account_id_type(accounting_export=accounting_export, export_settings=export_settings, merchant=lineitem.vendor)

            document_number = accounting_export.description['claim_number'] if accounting_export.description and accounting_export.description.get('claim_number') else accounting_export.description['expense_number']

            dimensions = self.get_dimension_object(accounting_export, lineitem)

            journal_entry_lineitems_object, _ = JournalEntryLineItems.objects.update_or_create(
                journal_entry_id = journal_entry.id,
                expense_id=lineitem.id,
                defaults={
                    'amount': lineitem.amount * -1,
                    'account_id': account_id,
                    'account_type': account_type,
                    'document_number':  document_number,
                    'accounts_payable_account_id': account.destination_account.destination_id,
                    'comment': comment,
                    'workspace_id': accounting_export.workspace_id,
                    'invoice_date': invoice_date,
                    'description': lineitem.purpose if lineitem.purpose else None,
                    'dimensions': dimensions
                }
            )
            journal_entry_lineitems.append(journal_entry_lineitems_object)

        return journal_entry_lineitems
