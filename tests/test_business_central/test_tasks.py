from apps.business_central.exports.journal_entry.tasks import ExportJournalEntry
from apps.business_central.exports.purchase_invoice.tasks import ExportPurchaseInvoice
from apps.business_central.exports.journal_entry.models import JournalEntry, JournalEntryLineItems
from apps.business_central.exports.purchase_invoice.models import PurchaseInvoice, PurchaseInvoiceLineitems
from apps.accounting_exports.models import AccountingExport
from apps.business_central.exports.journal_entry.tasks import create_journal_entry
from apps.business_central.exports.purchase_invoice.tasks import create_purchase_invoice


def test_trigger_export_journal_entry(db, mocker):
    '''
    Test trigger_export method of ExportJournalEntry class
    Just for coverage
    '''

    mocker.patch(
        'apps.business_central.exports.journal_entry.queues.check_accounting_export_and_start_import'
    )

    export_journal_entry = ExportJournalEntry()
    export_journal_entry.trigger_export(1, [1], False, 0)

    assert True


def test_construct_journal_entry(
    db,
    mocker,
    create_journal_line_items
):
    '''
    Test __construct_journal_entry method of ExportJournalEntry class
    '''
    workspace_id = 1
    journal_entry = JournalEntry.objects.filter(workspace_id=workspace_id).first()
    lineitems = JournalEntryLineItems.objects.filter(workspace_id=workspace_id)

    export_journal_entry = ExportJournalEntry()
    payload_list = export_journal_entry._ExportJournalEntry__construct_journal_entry(journal_entry, lineitems)

    assert len(payload_list) > 0
    payload = payload_list[0]

    assert payload['accountType'] == journal_entry.account_type
    assert payload['accountNumber'] == journal_entry.account_id
    assert payload['postingDate'] == journal_entry.invoice_date
    assert payload['documentNumber'] == journal_entry.document_number


def test_post_export_journal_entry(
    db,
    mocker,
    create_temp_workspace,
    add_business_central_creds,
    create_export_settings,
    create_accounting_export_expenses,
    create_journal_line_items
):
    '''
    Test post_export method of ExportJournalEntry class
    '''
    workspace_id = 1
    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()
    journal_entry = JournalEntry.objects.filter(workspace_id=workspace_id).first()
    lineitems = JournalEntryLineItems.objects.filter(workspace_id=workspace_id)

    mocker_instance = mocker.MagicMock()

    mocker.patch(
        'apps.business_central.exports.journal_entry.tasks.BusinessCentralConnector',
        return_value=mocker_instance
    )

    mocker_instance.bulk_post_journal_lineitems.return_value = {
        "responses": [
            {
                "body": {
                    "id": 12345
                }
            },
            {
                "body": {
                    "id": 67890
                }
            }
        ]
    }

    mocker.patch(
        'apps.business_central.exports.helpers.load_attachments'
    )

    export_journal_entry = ExportJournalEntry()
    response = export_journal_entry.post(accounting_export, journal_entry, lineitems)

    assert len(response["responses"]) == 2
    assert response['responses'][0]['body']['id'] == 12345
    assert response['responses'][1]['body']['id'] == 67890


def test_create_journal_entry(
    db,
    mocker,
    create_temp_workspace,
    create_export_settings,
    create_accounting_export_expenses,
    add_accounting_export_summary
):
    '''
    Test create_journal_entry method of ExportJournalEntry class
    '''
    workspace_id = 1
    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()

    mocker_instance = mocker.MagicMock()
    mocker.patch(
        'apps.business_central.exports.journal_entry.tasks.ExportJournalEntry',
        return_value=mocker_instance
    )

    mocker_instance.create_business_central_object.return_value = {
        "id": 12345,
        "dummy_key": "dummy_value"
    }

    exported_journal_entry = create_journal_entry(accounting_export, True)

    assert exported_journal_entry['id'] == 12345
    assert exported_journal_entry['dummy_key'] == "dummy_value"


def test_trigger_export_purchase_invoice(db, mocker):
    '''
    Test trigger_export method of ExportPurchaseInvoice class
    Just for coverage
    '''

    mocker.patch(
        'apps.business_central.exports.purchase_invoice.queues.check_accounting_export_and_start_import'
    )

    export_purchase_invoice = ExportPurchaseInvoice()
    export_purchase_invoice.trigger_export(1, [1], False, 0)

    assert True


def test_construct_purchase_invoice(
    db,
    mocker,
    create_purchase_invoice_line_items
):
    '''
    Test __construct_purchase_invoice method of ExportPurchaseInvoice class
    '''

    workspace_id = 1
    purchase_invoice = PurchaseInvoice.objects.filter(workspace_id=workspace_id).first()
    lineitems = PurchaseInvoiceLineitems.objects.filter(workspace_id=workspace_id)

    export_purchase_invoice = ExportPurchaseInvoice()
    payload, batch_payload = export_purchase_invoice.\
        _ExportPurchaseInvoice__construct_purchase_invoice(
            purchase_invoice,
            lineitems
        )

    assert payload['vendorNumber'] == purchase_invoice.vendor_number
    assert payload['invoiceDate'] == purchase_invoice.invoice_date

    assert len(batch_payload) > 0
    assert batch_payload[0]['lineType'] == 'Account'
    assert batch_payload[0]['lineObjectNumber'] == lineitems[0].accounts_payable_account_id
    assert batch_payload[0]['unitCost'] == lineitems[0].amount


def test_post_export_purchase_invoice(
    db,
    mocker,
    create_temp_workspace,
    add_business_central_creds,
    create_export_settings,
    create_accounting_export_expenses,
    create_purchase_invoice,
    create_purchase_invoice_line_items
):
    '''
    Test post_export method of ExportPurchaseInvoice class
    '''
    workspace_id = 1
    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()
    purchase_invoice = PurchaseInvoice.objects.filter(workspace_id=workspace_id).first()
    lineitems = PurchaseInvoiceLineitems.objects.filter(workspace_id=workspace_id)

    mocker_instance = mocker.MagicMock()

    mocker.patch(
        'apps.business_central.exports.purchase_invoice.tasks.BusinessCentralConnector',
        return_value=mocker_instance
    )

    mocker_instance.post_purchase_invoice.return_value = {
        "purchase_invoice_response": {
            "id": 12345
        }
    }

    mocker.patch(
        'apps.business_central.exports.helpers.load_attachments'
    )

    export_purchase_invoice = ExportPurchaseInvoice()
    response = export_purchase_invoice.post(accounting_export, purchase_invoice, lineitems)

    assert response['purchase_invoice_response']['id'] == 12345

    mocker_instance.post_purchase_invoice.return_value = {
        "purchase_invoice_response": {
            "id": 67890
        }
    }

    lineitems.location_id = 'dummy_location_id'
    response = export_purchase_invoice.post(accounting_export, purchase_invoice, lineitems)

    assert response['purchase_invoice_response']['id'] == 67890


def test_create_purchase_invoice(
    db,
    mocker,
    create_temp_workspace,
    create_export_settings,
    create_accounting_export_expenses,
    add_accounting_export_summary
):
    '''
    Test create_purchase_invoice method of ExportPurchaseInvoice class
    '''
    workspace_id = 1
    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()

    mocker_instance = mocker.MagicMock()
    mocker.patch(
        'apps.business_central.exports.purchase_invoice.tasks.ExportPurchaseInvoice',
        return_value=mocker_instance
    )

    mocker_instance.create_business_central_object.return_value = {
        "id": 12345,
        "dummy_key": "dummy_value"
    }

    exported_purchase_invoice = create_purchase_invoice(accounting_export, True)

    assert exported_purchase_invoice['id'] == 12345
    assert exported_purchase_invoice['dummy_key'] == "dummy_value"
