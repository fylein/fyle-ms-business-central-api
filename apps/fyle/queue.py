"""
All the tasks which are queued into django-q
    * User Triggered Async Tasks
    * Schedule Triggered Async Tasks
"""
from django_q.tasks import async_task

from apps.accounting_exports.models import AccountingExport
from apps.fyle.tasks import import_expenses
from apps.workspaces.models import Workspace


def queue_import_reimbursable_expenses(workspace_id: int, synchronous: bool = False):
    """
    Queue Import of Reimbursable Expenses from Fyle
    :param workspace_id: Workspace id
    :return: None
    """
    accounting_export, _ = AccountingExport.objects.update_or_create(
        workspace_id=workspace_id,
        type='FETCHING_REIMBURSABLE_EXPENSES',
        defaults={
            'status': 'IN_PROGRESS'
        }
    )

    if not synchronous:
        async_task(
            'apps.fyle.tasks.import_expenses',
            workspace_id, accounting_export, 'PERSONAL_CASH_ACCOUNT', 'PERSONAL'
        )
        return

    import_expenses(workspace_id, accounting_export, 'PERSONAL_CASH_ACCOUNT', 'PERSONAL')


def queue_import_credit_card_expenses(workspace_id: int, synchronous: bool = False):
    """
    Queue Import of Credit Card Expenses from Fyle
    :param workspace_id: Workspace id
    :return: None
    """
    accounting_export, _ = AccountingExport.objects.update_or_create(
        workspace_id=workspace_id,
        type='FETCHING_CREDIT_CARD_EXPENSES',
        defaults={
            'status': 'IN_PROGRESS'
        }
    )

    if not synchronous:
        async_task(
            'apps.fyle.tasks.import_expenses',
            workspace_id, accounting_export, 'PERSONAL_CORPORATE_CREDIT_CARD_ACCOUNT', 'CCC'
        )
        return

    import_expenses(workspace_id, accounting_export, 'PERSONAL_CORPORATE_CREDIT_CARD_ACCOUNT', 'CCC')


def async_handle_webhook_callback(body: dict) -> None:
    """
    Async'ly import and export expenses
    :param body: body
    :return: None
    """
    if body.get('action') == 'ACCOUNTING_EXPORT_INITIATED' and body.get('data'):
        org_id = body['data']['org_id']
        workspace = Workspace.objects.get(org_id=org_id)
        async_task('apps.workspaces.tasks.run_import_export', workspace.id)
