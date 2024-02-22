from apps.workspaces.tasks import (
    async_update_fyle_credentials,
    run_import_export,
    schedule_sync,
    export_to_business_central
)
from apps.accounting_exports.models import AccountingExport, AccountingExportSummary
from apps.business_central.exports.journal_entry.tasks import ExportJournalEntry
from apps.business_central.exports.purchase_invoice.tasks import ExportPurchaseInvoice
from apps.workspaces.models import FyleCredential

def test_async_update_fyle_credentials(
    db,
    mocker,
    create_temp_workspace,
    add_fyle_credentials
):
    workspace_id = 1
    org_id = "riseabovehate1"

    async_update_fyle_credentials(
        fyle_org_id=org_id,
        refresh_token="refresh_token"
    )

    fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)
    assert fyle_credentials.refresh_token == "refresh_token"
