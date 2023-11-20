"""
All the tasks which are queued into django-q
    * User Triggered Async Tasks
    * Schedule Triggered Async Tasks
"""
from django_q.tasks import async_task

from apps.accounting_exports.models import AccountingExport
from apps.fyle.tasks import import_expenses


def queue_import_expenses(workspace_id: int, synchronous: bool = False):
    """
    Queue Import of Expenses from Fyle
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
            workspace_id, accounting_export, 'PERSONAL_CASH_ACCOUNT', 'PERSONAL'
        )
        async_task(
            'apps.fyle.tasks.import_expenses',
            workspace_id, accounting_export, 'PERSONAL_CORPORATE_CREDIT_CARD_ACCOUNT', 'CCC'
        )
        return

    import_expenses(workspace_id, accounting_export, 'PERSONAL_CASH_ACCOUNT', 'PERSONAL')
    import_expenses(workspace_id, accounting_export, 'PERSONAL_CORPORATE_CREDIT_CARD_ACCOUNT', 'CCC')
