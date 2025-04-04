from datetime import datetime

from django.db import models
from django.db.models import Sum
from fyle_accounting_mappings.models import DestinationAttribute, EmployeeMapping, ExpenseAttribute, Mapping, MappingSetting

from apps.accounting_exports.models import AccountingExport
from apps.fyle.models import Expense
from apps.workspaces.models import AdvancedSetting, ExportSetting, FyleCredential, Workspace


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

        expense_link = '{0}/app/admin/#/enterprise/view_expense/{1}?org_id={2}'.format(
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

    def get_account_id_type(accounting_export: AccountingExport, export_settings: ExportSetting, merchant: str = None) -> str:
        mapping = EmployeeMapping.objects.filter(
            source_employee__value=accounting_export.description.get('employee_email'),
            workspace_id=accounting_export.workspace_id
        ).first()

        def get_vendor_or_employee_id(employee_field_mapping: str, mapping: EmployeeMapping) -> str:
            if employee_field_mapping == 'VENDOR':
                return "Vendor", mapping.destination_vendor.destination_id
            else:
                return "Employee", mapping.destination_employee.destination_id

        if export_settings.reimbursable_expenses_export_type == 'PURCHASE_INVOICE' and accounting_export.fund_source == 'PERSONAL':
            return "", mapping.destination_vendor.destination_id
        else:
            if accounting_export.fund_source == 'PERSONAL':
                return get_vendor_or_employee_id(export_settings.employee_field_mapping, mapping)
            else:
                if export_settings.name_in_journal_entry == 'MERCHANT':
                    if merchant:
                        vendor = DestinationAttribute.objects.filter(
                            value__iexact=merchant, attribute_type='VENDOR', workspace_id=accounting_export.workspace_id
                        ).first()
                        return "Vendor", vendor.destination_id if vendor else export_settings.default_vendor_id
                    else:
                        return "Vendor", export_settings.default_vendor_id
                else:
                    return get_vendor_or_employee_id(export_settings.employee_field_mapping, mapping)

    def get_expense_purpose(lineitem: Expense, category: str, advance_setting: AdvancedSetting) -> str:
        memo_structure = advance_setting.expense_memo_structure
        lineitem_purpose = ''

        if lineitem.purpose and len(lineitem.purpose) > 40:
            lineitem_purpose = lineitem.purpose[:37] + '...'
        else:
            lineitem_purpose = lineitem.purpose

        details = {
            'employee_email': lineitem.employee_email,
            'merchant': '{0}'.format(lineitem.vendor) if lineitem.vendor else '',
            'category': '{0}'.format(category) if lineitem.category else '',
            'purpose': '{0}'.format(lineitem_purpose),
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

    def get_location_id(accounting_export: AccountingExport, lineitem: Expense):
        location_id = None

        location_setting: MappingSetting = MappingSetting.objects.filter(
            workspace_id=accounting_export.workspace_id,
            destination_field='LOCATION'
        ).first()

        if location_setting:
            if location_setting.source_field == 'PROJECT':
                source_value = lineitem.project
            elif location_setting.source_field == 'COST_CENTER':
                source_value = lineitem.cost_center
            else:
                attribute = ExpenseAttribute.objects.filter(attribute_type=location_setting.source_field, workspace_id=accounting_export.workspace_id).first()
                source_value = lineitem.custom_properties.get(attribute.display_name, None)

            mapping: Mapping = Mapping.objects.filter(
                source_type=location_setting.source_field,
                destination_type='LOCATION',
                source__value=source_value,
                workspace_id=accounting_export.workspace_id
            ).first()

            if mapping:
                location_id = mapping.destination.destination_id
        return location_id

    def get_dimension_object(accounting_export: AccountingExport, lineitem: Expense):
        mapping_settings = MappingSetting.objects.filter(workspace_id=accounting_export.workspace_id).all()

        dimensions = []
        default_expense_attributes = ['CATEGORY', 'EMPLOYEE']
        default_destination_attributes = ['COMPANIES', 'ACCOUNTS', 'VENDORS', 'EMPLOYEES', 'LOCATIONS', 'BANK_ACCOUNTS']

        for setting in mapping_settings:
            if setting.source_field not in default_expense_attributes and \
                    setting.destination_field not in default_destination_attributes:
                if setting.source_field == 'PROJECT':
                    source_value = lineitem.project
                elif setting.source_field == 'COST_CENTER':
                    source_value = lineitem.cost_center
                else:
                    attribute = ExpenseAttribute.objects.filter(
                        attribute_type=setting.source_field,
                        workspace_id=accounting_export.workspace_id
                    ).first()
                    source_value = lineitem.custom_properties.get(attribute.display_name, None)

                mapping: Mapping = Mapping.objects.filter(
                    source_type=setting.source_field,
                    destination_type=setting.destination_field,
                    source__value=source_value,
                    workspace_id=accounting_export.workspace_id
                ).first()

                if mapping:
                    dimension_data = {
                        'id': mapping.destination.detail['dimension_id'],
                        'code': mapping.destination.attribute_type,
                        'valueId': mapping.destination.destination_id,
                        'valueCode': mapping.destination.detail['code'],
                        'expense_number': lineitem.expense_number
                    }
                    dimensions.append(dimension_data)

        return dimensions
