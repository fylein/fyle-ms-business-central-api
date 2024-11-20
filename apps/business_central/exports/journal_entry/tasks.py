import logging
from typing import Dict, List

from apps.accounting_exports.models import AccountingExport
from apps.business_central.actions import update_accounting_export_summary
from apps.business_central.exceptions import handle_business_central_exceptions
from apps.business_central.exports.accounting_export import AccountingDataExporter
from apps.business_central.exports.helpers import load_attachments
from apps.business_central.exports.journal_entry.models import JournalEntry, JournalEntryLineItems
from apps.business_central.exports.journal_entry.queues import check_accounting_export_and_start_import
from apps.business_central.utils import BusinessCentralConnector
from apps.workspaces.models import BusinessCentralCredentials

logger = logging.getLogger(__name__)
logger.level = logging.INFO


class ExportJournalEntry(AccountingDataExporter):
    '''
    Class for handling the export of journal entry to Business Central.
    Extends the base AccountingDataExporter class.
    '''

    def __init__(self):
        super().__init__()  # Call the constructor of the parent class
        self.body_model = JournalEntry
        self.lineitem_model = JournalEntryLineItems

    def trigger_export(self, workspace_id, accounting_export_ids, is_auto_export, interval_hours):
        '''
        Trigger the import process for the Project module.
        '''
        check_accounting_export_and_start_import(workspace_id=workspace_id, accounting_export_ids=accounting_export_ids, is_auto_export=is_auto_export, interval_hours=interval_hours)

    def __construct_journal_entry(self, body: JournalEntry, lineitems: List[JournalEntryLineItems]) -> Dict:
        '''
        Construct the payload for the direct invoice.
        :param expense_report: ExpenseReport object extracted from database
        :param expense_report_lineitems: ExpenseReportLineitem objects extracted from database
        :return: constructed expense_report
        '''
        batch_journal_entry_payload = []
        dimensions = []

        journal_entry_payload = {
            'accountType': body.account_type,
            'accountNumber': body.account_id,
            'postingDate': body.invoice_date,
            'documentNumber': body.document_number,
            'amount': body.amount,
            'comment': body.comment,
            'description': body.description,
            'balanceAccountType': 'G/L Account',
            'balancingAccountNumber': body.accounts_payable_account_id

        }

        batch_journal_entry_payload.append(journal_entry_payload)

        for lineitem in lineitems:
            for dimension in lineitem.dimensions:
                dimension['exported_module_id'] = lineitem.id

            dimensions.extend(lineitem.dimensions)
            journal_entry_lineitem_payload = {
                'accountType': lineitem.account_type,
                'accountNumber': lineitem.account_id,
                'postingDate': lineitem.invoice_date,
                'documentNumber': lineitem.document_number,
                'amount': lineitem.amount,
                'comment': lineitem.comment,
                'description': lineitem.description if lineitem.description else '',
                'balanceAccountType': 'G/L Account',
                'balancingAccountNumber': lineitem.accounts_payable_account_id
            }

            batch_journal_entry_payload.append(journal_entry_lineitem_payload)

        return batch_journal_entry_payload, dimensions

    def post(self, accounting_export, item, lineitem):
        '''
        Export the Journal Entry to Business Central.
        '''

        batch_journal_entry_payload, dimensions = self.__construct_journal_entry(item, lineitem)
        logger.info('WORKSPACE_ID: {0}, ACCOUNTING_EXPORT_ID: {1}, JOURNAL_ENTRY_PAYLOAD: {2}'.format(accounting_export.workspace_id, accounting_export.id, batch_journal_entry_payload))
        business_central_credentials = BusinessCentralCredentials.get_active_business_central_credentials(accounting_export.workspace_id)
        # Establish a connection to Business Central
        business_central_connection = BusinessCentralConnector(business_central_credentials, accounting_export.workspace_id)

        # Post the journal entry to Business Central
        response = business_central_connection.bulk_post_journal_lineitems(batch_journal_entry_payload, accounting_export)


        if dimensions:
            dimension_set_line_payloads = self.construct_dimension_set_line_payload(dimensions, response['responses'])
            logger.info('WORKSPACE_ID: {0}, ACCOUNTING_EXPORT_ID: {1}, DIMENSION_SET_LINE_PAYLOADS: {2}'.format(accounting_export.workspace_id, accounting_export.id, dimension_set_line_payloads))
            dimension_line_responses = (
                business_central_connection.post_dimension_lines(
                    dimension_set_line_payloads, "JOURNAL_ENTRY"
                )
            )
            response["dimension_line_responses"] = dimension_line_responses
        

        expenses = accounting_export.expenses.all()

        # Load attachments to Business Central
        for i in range(1, len(response["responses"])):
            load_attachments(
                business_central_connection,
                response["responses"][i]["body"]["id"],
                "Journal",
                expenses[i - 1],
                accounting_export)

        return response
    
    def construct_dimension_set_line_payload(self, dimensions: list, exported_response: dict):
        """
        construct payload for setting dimension for Purchase Invoice
        """

        dimension = dimensions[0]

        #we are only supporting grouping by expense for JE, so only two payloads will always exist
        # one for each line
        dimension_payload = [
            {
                "id": dimension['id'],
                "code": dimension['code'],
                "parentId": exported_response[0]['body']['id'],
                "valueId": dimension['valueId'],
                "valueCode": dimension['valueCode'],
                "exported_module_id": dimension['exported_module_id']
            },
            {
                "id": dimension['id'],
                "code": dimension['code'],
                "parentId": exported_response[1]['body']['id'],
                "valueId": dimension['valueId'],
                "valueCode": dimension['valueCode'],
                "exported_module_id": dimension['exported_module_id']
            }]

        return dimension_payload


@handle_business_central_exceptions()
def create_journal_entry(accounting_export: AccountingExport, last_export: bool):
    '''
    Helper function to create and export a journal entry.
    '''
    export_journal_entry_instance = ExportJournalEntry()

    # Create and export the journal entry using the base class method
    exported_jornal_entry = export_journal_entry_instance.create_business_central_object(accounting_export=accounting_export)

    if last_export:
        update_accounting_export_summary(accounting_export.workspace_id)

    return exported_jornal_entry
