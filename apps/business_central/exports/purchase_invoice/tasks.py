import logging
from datetime import datetime
from typing import Dict, List

from apps.accounting_exports.models import AccountingExport
from apps.business_central.actions import update_accounting_export_summary
from apps.business_central.exceptions import handle_business_central_exceptions
from apps.business_central.exports.accounting_export import AccountingDataExporter
from apps.business_central.exports.helpers import load_attachments
from apps.business_central.exports.purchase_invoice.models import PurchaseInvoice, PurchaseInvoiceLineitems
from apps.business_central.exports.purchase_invoice.queues import check_accounting_export_and_start_import
from apps.business_central.utils import BusinessCentralConnector
from apps.workspaces.models import BusinessCentralCredentials

logger = logging.getLogger(__name__)
logger.level = logging.INFO


class ExportPurchaseInvoice(AccountingDataExporter):
    '''
    Class for handling the export of Purchase Invoice to Business Central.
    Extends the base AccountingDataExporter class.
    '''

    def __init__(self):
        super().__init__()  # Call the constructor of the parent class
        self.body_model = PurchaseInvoice
        self.lineitem_model = PurchaseInvoiceLineitems

    def trigger_export(self, workspace_id, accounting_export_ids, is_auto_export, interval_hours):
        '''
        Trigger the import process for the Project module.
        '''
        check_accounting_export_and_start_import(workspace_id=workspace_id, accounting_export_ids=accounting_export_ids, is_auto_export=is_auto_export, interval_hours=interval_hours)

    def __construct_purchase_invoice(self, body: PurchaseInvoice, lineitems: List[PurchaseInvoiceLineitems]) -> Dict:
        '''
        Construct the payload for the direct invoice.
        :param expense_report: ExpenseReport object extracted from database
        :param expense_report_lineitems: ExpenseReportLineitem objects extracted from database
        :return: constructed expense_report
        '''
        batch_purchase_invoice_lineitem_payload = []
        dimensions = []

        purchase_invoice_payload = {
            'vendorNumber': body.vendor_number,
            'invoiceDate': body.invoice_date,
            'postingDate': datetime.now().strftime("%Y-%m-%d")
        }

        for lineitem in lineitems:
            for dimension in lineitem.dimensions:
                dimension['exported_module_id'] = lineitem.id

            print('lineitem.dimensions', lineitem.dimensions)

            dimensions.extend(lineitem.dimensions)
            purchase_invoice_lineitem_payload = {
                "lineType": "Account",
                'lineObjectNumber': lineitem.accounts_payable_account_id,
                'unitCost': lineitem.amount,
                'quantity': 1,
                'description': lineitem.description if lineitem.description else '',
                'description2': lineitem.expense.expense_number
            }
            if lineitem.location_id:
                purchase_invoice_lineitem_payload['locationId'] = lineitem.location_id

            batch_purchase_invoice_lineitem_payload.append(purchase_invoice_lineitem_payload)

        return purchase_invoice_payload, batch_purchase_invoice_lineitem_payload, dimensions


    def post(self, accounting_export, item, lineitem):
        '''
        Export the Journal Entry to Business Central.
        '''

        purchase_invoice_payload, batch_purchase_invoice_payload, dimensions = self.__construct_purchase_invoice(item, lineitem)
        logger.info('WORKSPACE_ID: {0}, ACCOUNTING_EXPORT_ID: {1}, PURCHASE_INVOICE_PAYLOAD: {2}, BATCH_PURCHASE_INVOICE_PAYLOAD: {3}'.format(accounting_export.workspace_id, accounting_export.id, purchase_invoice_payload, batch_purchase_invoice_payload))
        business_central_credentials = BusinessCentralCredentials.get_active_business_central_credentials(accounting_export.workspace_id)
        # Establish a connection to Business Central
        business_central_connection = BusinessCentralConnector(business_central_credentials, accounting_export.workspace_id)

        response = business_central_connection.post_purchase_invoice(purchase_invoice_payload, batch_purchase_invoice_payload)

        if dimensions:
            dimension_set_line_payloads = self.construct_dimension_set_line_payload(dimensions, response['bulk_post_response']['responses'])
            logger.info('WORKSPACE_ID: {0}, ACCOUNTING_EXPORT_ID: {1}, DIMENSION_SET_LINE_PAYLOADS: {2}'.format(accounting_export.workspace_id, accounting_export.id, dimension_set_line_payloads))
            dimension_line_responses = business_central_connection.post_dimension_lines(
                dimension_set_line_payloads, 'PURCHASE_INVOICE', item.id
            )
            response['dimension_line_responses'] = dimension_line_responses

        expenses = accounting_export.expenses.all()

        # Load attachments to Business Central
        for expense in expenses:
            load_attachments(
                business_central_connection,
                response["purchase_invoice_response"]["id"],
                "Purchase Invoice",
                expense,
                accounting_export)

        return response

    def construct_dimension_set_line_payload(self, dimensions: list, exported_response: dict):

        """
        construct payload for setting dimension for Purchase Invoice
        """

        dimension_payload = []

        document_mapping = {
            response['body']['description2']: response['body']['id']
            for response in exported_response
            if response.get('body') and 'description2' in response['body'] and 'id' in response['body']
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
                    "valueCode": dimension['valueCode'],
                    "exported_module_id": dimension['exported_module_id']
                })

        return dimension_payload


@handle_business_central_exceptions()
def create_purchase_invoice(accounting_export: AccountingExport, last_export: bool):
    '''
    Helper function to create and export a journal entry.
    '''
    export_purchase_invoice_instance = ExportPurchaseInvoice()

    # Create and export the journal entry using the base class method
    exported_purchase_invoice = export_purchase_invoice_instance.create_business_central_object(accounting_export=accounting_export)

    if last_export:
        update_accounting_export_summary(accounting_export.workspace_id)

    return exported_purchase_invoice
