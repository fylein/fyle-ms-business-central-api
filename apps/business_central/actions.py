from django.db.models import Q

from apps.accounting_exports.models import AccountingExport
from apps.workspaces.models import LastExportDetail


def update_last_export_details(workspace_id):
    last_export_detail = LastExportDetail.objects.get(workspace_id=workspace_id)

    failed_exports = AccountingExport.objects.filter(~Q(type__in=['FETCHING_REIMBURSABLE_EXPENSES', 'FETCHING_CREDIT_CARD_EXPENSES']), workspace_id=workspace_id, status__in=['FAILED', 'FATAL']).count()

    successful_exports = AccountingExport.objects.filter(
        ~Q(type__in=['FETCHING_REIMBURSABLE_EXPENSES', 'FETCHING_CREDIT_CARD_EXPENSES']),
        workspace_id=workspace_id, status='COMPLETE',
    ).count()

    last_export_detail.failed_accounting_exports_count = failed_exports
    last_export_detail.successful_accounting_exports_count = successful_exports
    last_export_detail.total_accounting_exports_count = failed_exports + successful_exports
    last_export_detail.save()

    return last_export_detail
