from typing import Dict

from apps.accounting_exports.models import AccountingExport
from apps.business_central.exceptions import handle_business_central_exceptions
from apps.business_central.exports.accounting_export import AccountingDataExporter
from apps.business_central.exports.journal_entry.models import JournalEntry
from apps.business_central.exports.journal_entry.queues import check_accounting_export_and_start_import
from apps.business_central.utils import BusinessCentralConnector
from apps.workspaces.models import BusinessCentralCredentials


class ExportJournalEntry(AccountingDataExporter):
    """
    Class for handling the export of journal entry to Business Central.
    Extends the base AccountingDataExporter class.
    """

    def __init__(self):
        super().__init__()  # Call the constructor of the parent class
        self.body_model = JournalEntry

    def trigger_export(self, workspace_id, accounting_export_ids):
        """
        Trigger the import process for the Project module.
        """
        check_accounting_export_and_start_import(workspace_id, accounting_export_ids)

    def __construct_journal_entry(self, body: JournalEntry) -> Dict:
        """
        Construct the payload for the direct invoice.
        :param expense_report: ExpenseReport object extracted from database
        :param expense_report_lineitems: ExpenseReportLineitem objects extracted from database
        :return: constructed expense_report
        """

        journal_entry_payload = {
            'accountNumber': body.accounts_payable_account_id,
            'postingDate': body.invoice_date,
            'documentNumber': None,
            'amount': body.amount,
            'comment': body.comment,
            'description': body.description
        }

        return journal_entry_payload

    def post(self, accounting_export, item, lineitem = None):
        """
        Export the Journal Entry to Business Central.
        """

        journal_entry_payload = self.__construct_journal_entry(item)
        business_central_credentials = BusinessCentralCredentials.objects.filter(workspace_id=accounting_export.workspace_id).first()
        # Establish a connection to Business Central
        business_central_connection = BusinessCentralConnector(business_central_credentials, accounting_export.workspace_id)

        # Post the journal entry to Business Central
        response = business_central_connection.connection.journal_line_items.post("b3c4303f-4319-ee11-9cc4-6045bdc8dcac", journal_entry_payload)

        return response


@handle_business_central_exceptions()
def create_journal_entry(accounting_export: AccountingExport):
    """
    Helper function to create and export a journal entry.
    """
    export_jouranl_entry_instance = ExportJournalEntry()

    # Create and export the journal entry using the base class method
    exported_jornal_entry = export_jouranl_entry_instance.create_business_central_object(accounting_export=accounting_export)

    return exported_jornal_entry
