from datetime import datetime

from django.db import models
from django.db.models import Sum

from apps.accounting_exports.models import AccountingExport
from apps.fyle.models import Expense
from apps.workspaces.models import AdvancedSetting, FyleCredential, Workspace


class BaseExportModel(models.Model):
    """
    Base Model for Business Central Export
    """
    created_at = models.DateTimeField(auto_now_add=True, help_text='Created at')
    updated_at = models.DateTimeField(auto_now=True, help_text='Updated at')
    workspace = models.ForeignKey(Workspace, on_delete=models.PROTECT, help_text='Reference to Workspace model')

    class Meta:
        abstract = True

    def get_expense_comment(workspace_id, lineitem: Expense, category: str, advance_setting: AdvancedSetting) -> str:
        workspace = Workspace.objects.get(id=workspace_id)
        org_id = workspace.org_id

        fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)
        cluster_domain = fyle_credentials.cluster_domain
        workspace.cluster_domain = cluster_domain
        workspace.save()

        expense_link = '{0}/app/main/#/enterprise/view_expense/{1}?org_id={2}'.format(
            cluster_domain, lineitem.expense_id, org_id
        )

        memo_structure = advance_setting.expense_memo_structure

        details = {
            'employee_email': lineitem.employee_email,
            'merchant': '{0}'.format(lineitem.vendor) if lineitem.vendor else '',
            'category': '{0}'.format(category) if lineitem.category else '',
            'purpose': '{0}'.format(lineitem.purpose) if lineitem.purpose else '',
            'report_number': '{0}'.format(lineitem.claim_number),
            'spent_on': '{0}'.format(lineitem.spent_at.date()) if lineitem.spent_at else '',
            'expense_link': expense_link
        }

        purpose = ''

        for id, field in enumerate(memo_structure):
            if field in details:
                purpose += details[field]
                if id + 1 != len(memo_structure):
                    purpose = '{0} - '.format(purpose)

        return purpose

    def get_total_amount(accounting_export: AccountingExport):
        """
         Calculate the total amount of expenses associated with a given AccountingExport

        Parameters:
        - accounting_export (AccountingExport): The AccountingExport instance for which to calculate the total amount.

        Returns:
        - float: The total amount of expenses associated with the provided AccountingExport.
        """

        # Using the related name 'expenses' to access the expenses associated with the given AccountingExport
        total_amount = accounting_export.expenses.aggregate(Sum('amount'))['amount__sum']

        # If there are no expenses for the given AccountingExport, 'total_amount' will be None
        # Handle this case by returning 0 or handling it as appropriate for your application
        return total_amount or 0.0

    def get_invoice_date(accounting_export: AccountingExport) -> str:
        """
        Get the invoice date from the provided AccountingExport.

        Parameters:
        - accounting_export (AccountingExport): The AccountingExport instance containing the description field.

        Returns:
        - str: The invoice date as a string in the format '%Y-%m-%dT%H:%M:%S'.
        """
        # Check for specific keys in the 'description' field and return the corresponding value
        if 'spent_at' in accounting_export.description and accounting_export.description['spent_at']:
            return accounting_export.description['spent_at']
        elif 'approved_at' in accounting_export.description and accounting_export.description['approved_at']:
            return accounting_export.description['approved_at']
        elif 'verified_at' in accounting_export.description and accounting_export.description['verified_at']:
            return accounting_export.description['verified_at']
        elif 'last_spent_at' in accounting_export.description and accounting_export.description['last_spent_at']:
            return accounting_export.description['last_spent_at']
        elif 'posted_at' in accounting_export.description and accounting_export.description['posted_at']:
            return accounting_export.description['posted_at']

        # If none of the expected keys are present or if the values are empty, return the current date and time
        return datetime.now().strftime("%Y-%m-%d")

    def get_vendor_id(accounting_export: AccountingExport) -> str:
        return "10040"

    def get_journal_entry_account_id_type(accounting_export: AccountingExport) -> str:
        return "EH", "Employee"

    def get_expense_purpose(lineitem: Expense, category: str, advance_setting: AdvancedSetting) -> str:
        memo_structure = advance_setting.expense_memo_structure

        details = {
            'employee_email': lineitem.employee_email,
            'merchant': '{0}'.format(lineitem.vendor) if lineitem.vendor else '',
            'category': '{0}'.format(category) if lineitem.category else '',
            'purpose': '{0}'.format(lineitem.purpose) if lineitem.purpose else '',
            'report_number': '{0}'.format(lineitem.claim_number),
            'spent_on': '{0}'.format(lineitem.spent_at.date()) if lineitem.spent_at else '',
        }

        purpose = ''

        for id, field in enumerate(memo_structure):
            if field in details:
                purpose += details[field]
                if id + 1 != len(memo_structure):
                    purpose = '{0} - '.format(purpose)

        return purpose
