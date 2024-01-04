from django.db import models
from fyle_accounting_mappings.models import CategoryMapping

from apps.accounting_exports.models import AccountingExport
from apps.business_central.exports.base_model import BaseExportModel
from apps.fyle.models import Expense
from apps.workspaces.models import AdvancedSetting
from ms_business_central_api.models.fields import CustomDateTimeField, FloatNullField, StringNullField, TextNotNullField


class PurchaseInvoice(BaseExportModel):
    """
    Purchase Invoice Model
    """

    accounting_export = models.OneToOneField(AccountingExport, on_delete=models.PROTECT, help_text='Accounting Export reference')
    accounting_date = CustomDateTimeField(help_text='accounting date of purchase invoice')
    amount = FloatNullField(help_text='Total Amount of the invoice')
    code = StringNullField(max_length=10, help_text='unique code for invoice')
    description = TextNotNullField(help_text='description for the invoice')
    invoice_date = CustomDateTimeField(help_text='date of invoice')
    tax_amount = FloatNullField(help_text='total tax amount of the invoice')
    vendor_id = StringNullField(help_text='id of vendor')

    class Meta:
        db_table = 'purchase_invoices'

    @classmethod
    def create_or_update_object(self, accounting_export: AccountingExport):
        """
        Create Purchase Invoice
        :param accounting_export: expense group
        :return: purchase invoices object
        """
        description = accounting_export.description

        vendor_id = self.get_vendor_id(accounting_export=accounting_export)
        amount = self.get_total_amount(accounting_export=accounting_export)
        invoice_date = self.get_invoice_date(accounting_export=accounting_export)

        purchase_invoice, _ = PurchaseInvoice.objects.update_or_create(
            accounting_export=accounting_export,
            defaults={
                'amount': amount,
                'vendor_id': vendor_id,
                'description': description,
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
    tax_amount = FloatNullField(help_text='tax amount of the invoice')

    class Meta:
        db_table = 'purchase_invoice_lineitems'

    @classmethod
    def create_or_update_object(self, accounting_export: AccountingExport, advance_setting: AdvancedSetting):
        """
        Create Purchase Invoice
        :param accounting_export: expense group
        :return: purchase invoices object
        """

        expenses = accounting_export.expenses.all()
        purchase_invoice = PurchaseInvoice.objects.get(accounting_export=accounting_export)

        purchase_invoice_lineitem_objects = []

        for lineitem in expenses:
            account = CategoryMapping.objects.filter(
                source_category__value=lineitem.category,
                workspace_id=accounting_export.workspace_id
            ).first()

            description = self.get_expense_purpose(accounting_export.workspace_id, lineitem, lineitem.category, advance_setting)

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
