# from django.db import models

# from apps.accounting_exports.models import AccountingExport
# from apps.business_central.exports.base_model import BaseExportModel
# from apps.fyle.models import Expense
# from ms_business_central_api.models.fields import CustomDateTimeField, FloatNullField, StringNullField, TextNotNullField, TextNullField


# class JournalEntry(BaseExportModel):
#     """
#     Journal Entry Model
#     """

#     accounts_payable_account_id = StringNullField(help_text='destination id of accounts payable account')
#     expense = models.OneToOneField(Expense, on_delete=models.PROTECT, help_text='Reference to Expense')
#     amount = FloatNullField(help_text='Amount of the invoice')
#     comment = TextNotNullField(help_text='description for the invoice')
#     description = TextNullField(help_text='description for the invoice')
#     invoice_date = CustomDateTimeField(help_text='date of invoice')
#     accounting_export = models.OneToOneField(AccountingExport, on_delete=models.PROTECT, help_text='Accounting Export reference')

#     class Meta:
#         db_table = 'journal_entries'
