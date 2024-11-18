from datetime import datetime

from django.db import transaction

from apps.accounting_exports.models import AccountingExport
from apps.business_central.exports.helpers import resolve_errors_for_exported_accounting_export, validate_accounting_export
from apps.workspaces.models import AdvancedSetting, ExportSetting


class AccountingDataExporter:
    """
    Base class for exporting accounting data to an external accounting system.
    Subclasses should implement the 'post' method for posting data.
    """

    def __init__(self):
        self.body_model = None
        self.lineitem_model = None

    def post(self, workspace_id, body, lineitems = None):
        """
        Implement this method to post data to the external accounting system.
        """
        raise NotImplementedError("Please implement this method")

    def create_business_central_object(self, accounting_export: AccountingExport):
        """
        Create a accounting expense in the external accounting system.

        Args:
            accounting_export (AccountingExport): The accounting export object.

        Raises:
            NotImplementedError: If the method is not implemented in the subclass.
        """
        # Retrieve advance settings for the current workspace
        advance_settings = AdvancedSetting.objects.filter(workspace_id=accounting_export.workspace_id).first()

        export_settings = ExportSetting.objects.filter(workspace_id=accounting_export.workspace_id).first()

        # Check and update the status of the accounting export
        if accounting_export.status not in ['IN_PROGRESS', 'COMPLETE']:
            accounting_export.status = 'IN_PROGRESS'
            accounting_export.save()
        else:
            # If the status is already 'IN_PROGRESS' or 'COMPLETE', return without further processing
            return

        validate_accounting_export(accounting_export, export_settings)
        with transaction.atomic():
            # Create or update the main body of the accounting object
            body_model_object = self.body_model.create_or_update_object(accounting_export, advance_settings, export_settings)

            # Create or update line items for the accounting object
            lineitems_model_objects = None
            if self.lineitem_model:
                lineitems_model_objects = self.lineitem_model.create_or_update_object(
                    accounting_export, advance_settings, export_settings
                )

            # Post the data to the external accounting system
            created_object = self.post(accounting_export, body_model_object, lineitems_model_objects)

            # Update the accounting export details
            detail = created_object

            accounting_export.detail = detail
            accounting_export.export_url = 'https://businesscentral.dynamics.com/'
            accounting_export.business_central_errors = None
            accounting_export.exported_at = datetime.now()
            accounting_export.status = 'COMPLETE'
            accounting_export.save()
            resolve_errors_for_exported_accounting_export(accounting_export)

    def __construct_dimension_set_line_payload(self, dimensions: list, exported_response: dict, exported_module: str):

        """
        construct payload for setting dimension for JE and Purchase Invoice
        """

        dimension_payload = []

        # for journal entry we will only support grouping by expense
        # so exported_response will always have 2 length and dimensions will have 1 length.
        if exported_module == 'JOURNAL_ENTRY':
            dimension = dimensions[0]
            for i in range(2):
                parent_id = exported_response[i]['body']['id']
                dimension_payload.append({
                    "id": dimension['id'],
                    "code": dimension['code'],
                    "parentId": parent_id,
                    "valueId": dimension['valueId'],
                    "valueCode": dimension['valueCode']
                })
            return dimension_payload

        document_mapping = {
            response['body']['documentNumber']: response['body']['id']
            for response in exported_response
            if response.get('body') and 'documentNumber' in response['body'] and 'id' in response['body']
        }

        for dimension in dimensions:
            expense_number = dimension.get('expense_number')
            parent_id = document_mapping.get(expense_number)

            if parent_id:
                dimension_payload.append({
                    "id": dimension['id'],
                    "code": dimension['code'],
                    "parentId": parent_id,
                    "valueId": dimension['valueId'],
                    "valueCode": dimension['valueCode']
                })

        return dimension_payload
