from typing import List

from django.db import models
from fyle_accounting_mappings.models import CategoryMapping

from apps.accounting_exports.models import AccountingExport
from apps.business_central.exports.base_model import BaseExportModel
from apps.fyle.models import Expense
from apps.workspaces.models import AdvancedSetting, ExportSetting
from ms_business_central_api.models.fields import CustomDateTimeField, FloatNullField, StringNullField, TextNotNullField


class PurchaseInvoice(BaseExportModel):
    """
    Purchase Invoice Model
    """

    accounting_export = models.OneToOneField(AccountingExport, on_delete=models.PROTECT, help_text='Accounting Export reference', related_name='purchase_invoice')
    accounting_date = CustomDateTimeField(help_text='accounting date of purchase invoice')
    amount = FloatNullField(help_text='Total Amount of the invoice')
    code = StringNullField(max_length=10, help_text='unique code for invoice')
    invoice_date = CustomDateTimeField(help_text='date of invoice')
    vendor_number = StringNullField(help_text='id of vendor')

    class Meta:
        db_table = 'purchase_invoices'

    @classmethod
    def create_or_update_object(self, accounting_export: AccountingExport, advance_setting: AdvancedSetting, export_settings: ExportSetting):
        """
        Create Purchase Invoice
        :param accounting_export: expense group
        :return: purchase invoices object
        """

        vendor_id = self.get_account_id_type(accounting_export=accounting_export, export_settings=export_settings)
        amount = self.get_total_amount(accounting_export=accounting_export)
        invoice_date = self.get_invoice_date(accounting_export=accounting_export)

        purchase_invoice, _ = PurchaseInvoice.objects.update_or_create(
            accounting_export=accounting_export,
            defaults={
                'amount': amount,
                'vendor_number': vendor_id,
                'invoice_date': invoice_date,
                'workspace_id': accounting_export.workspace_id
            }
        )

        return purchase_invoice


class PurchaseInvoiceLineitems(BaseExportModel):
    """
    Purchase Invoice Lineitem Model
    """

    accounts_payable_account_id = StringNullField(help_text='destination id of accounts payable account')
    purchase_invoice = models.ForeignKey(PurchaseInvoice, on_delete=models.PROTECT, help_text='Reference to PurchaseInvoice')
    expense = models.OneToOneField(Expense, on_delete=models.PROTECT, help_text='Reference to Expense')
    amount = FloatNullField(help_text='Amount of the invoice')
    description = TextNotNullField(help_text='description for the invoice')

    class Meta:
        db_table = 'purchase_invoice_lineitems'

    @classmethod
    def create_or_update_object(self, accounting_export: AccountingExport, advance_setting: AdvancedSetting, export_settings: ExportSetting):
        """
        Create Purchase Invoice
        :param accounting_export: expense group
        :return: purchase invoices object
        """

        expenses: List[Expense] = accounting_export.expenses.all()
        purchase_invoice = PurchaseInvoice.objects.get(accounting_export=accounting_export)

        purchase_invoice_lineitem_objects = []

        for lineitem in expenses:
            account = CategoryMapping.objects.filter(
                source_category__value=lineitem.category,
                workspace_id=accounting_export.workspace_id
            ).first()

            description = self.get_expense_purpose(lineitem, lineitem.category, advance_setting)

            purchase_invoice_lineitem_object, _ = PurchaseInvoiceLineitems.objects.update_or_create(
                purchase_invoice_id=purchase_invoice.id,
                expense_id=lineitem.id,
                defaults={
                    'amount': lineitem.amount,
                    'accounts_payable_account_id': account.destination_account.destination_id if account else None,
                    'description': description,
                    'workspace_id': accounting_export.workspace_id
                }
            )
            purchase_invoice_lineitem_objects.append(purchase_invoice_lineitem_object)

        return purchase_invoice_lineitem_objects
