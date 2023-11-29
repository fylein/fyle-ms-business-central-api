import logging
from datetime import datetime

from django.db import transaction
from fyle_integrations_platform_connector import PlatformConnector

from apps.accounting_exports.models import AccountingExport
from apps.fyle.exceptions import handle_exceptions
from apps.fyle.models import Expense
from apps.workspaces.models import ExportSetting, FyleCredential, Workspace

SOURCE_ACCOUNT_MAP = {
    'PERSONAL': 'PERSONAL_CASH_ACCOUNT',
    'CCC': 'PERSONAL_CORPORATE_CREDIT_CARD_ACCOUNT'
}

logger = logging.getLogger(__name__)
logger.level = logging.INFO


@handle_exceptions
def import_expenses(workspace_id, accounting_export: AccountingExport, source_account_type, fund_source_key):
    """
    Common logic for importing expenses from Fyle
    :param accounting_export: Task log object
    :param workspace_id: workspace id
    :param source_account_type: Fyle source account type
    :param fund_source_key: Key for accessing fund source specific fields in ExportSetting
    """

    fund_source_map = {
        'PERSONAL': 'reimbursable',
        'CCC': 'credit_card'
    }
    export_settings = ExportSetting.objects.get(workspace_id=workspace_id)
    workspace = Workspace.objects.get(pk=workspace_id)
    last_synced_at = getattr(workspace, f"{fund_source_map.get(fund_source_key)}_last_synced_at", None)
    fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)

    platform = PlatformConnector(fyle_credentials)

    expenses = platform.expenses.get(
        source_account_type=[source_account_type],
        state=getattr(export_settings, f"{fund_source_map.get(fund_source_key)}_expense_state"),
        settled_at=last_synced_at if getattr(export_settings, f"{fund_source_map.get(fund_source_key)}_expense_state") == 'PAYMENT_PROCESSING' else None,
        approved_at=last_synced_at if getattr(export_settings, f"{fund_source_map.get(fund_source_key)}_expense_state") == 'APPROVED' else None,
        filter_credit_expenses=(fund_source_key == 'CCC'),
        last_paid_at=last_synced_at if getattr(export_settings, f"{fund_source_map.get(fund_source_key)}_expense_state") == 'PAID' else None
    )

    if expenses:
        setattr(workspace, f"{fund_source_map.get(fund_source_key)}_last_synced_at", datetime.now())
        workspace.save()

    with transaction.atomic():
        expenses_object = Expense.create_expense_objects(expenses, workspace_id)
        AccountingExport.create_accounting_export(
            expenses_object,
            fund_source=fund_source_key,
            workspace_id=workspace_id
        )

    accounting_export.status = 'COMPLETE'
    accounting_export.business_central_errors = None

    accounting_export.save()