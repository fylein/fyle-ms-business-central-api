from typing import List
import logging

from django.db.models import Q
from django_q.tasks import Chain

from apps.accounting_exports.models import AccountingExport, Error
from apps.business_central.exports.helpers import validate_failing_export
from apps.workspaces.models import FyleCredential

logger = logging.getLogger(__name__)
logger.level = logging.INFO


def check_accounting_export_and_start_import(workspace_id: int, accounting_export_ids: List[str], is_auto_export: bool, interval_hours: int):
    """
    Check accounting export group and start export
    """

    fyle_credentials = FyleCredential.objects.filter(workspace_id=workspace_id).first()

    accounting_exports = AccountingExport.objects.filter(~Q(status__in=['IN_PROGRESS', 'COMPLETE', 'EXPORT_QUEUED']),
        workspace_id=workspace_id, id__in=accounting_export_ids, purchase_invoice__id__isnull=True, exported_at__isnull=True).all()

    errors = Error.objects.filter(workspace_id=workspace_id, is_resolved=False, accounting_export_id__in=accounting_export_ids).all()

    chain = Chain()
    chain.append('apps.fyle.helpers.sync_dimensions', fyle_credentials)

    for index, accounting_export_group in enumerate(accounting_exports):
        error = errors.filter(workspace_id=workspace_id, accounting_export=accounting_export_group, is_resolved=False).first()
        skip_export = validate_failing_export(is_auto_export, interval_hours, error)
        if skip_export:
            logger.info('Skipping expense group %s as it has %s errors', accounting_export_group.id, error.repetition_count)
            continue
        accounting_export, _ = AccountingExport.objects.update_or_create(
            workspace_id=accounting_export_group.workspace_id,
            id=accounting_export_group.id,
            defaults={
                'status': 'ENQUEUED',
                'type': 'PURCHASE_INVOICE'
            }
        )

        if accounting_export.status not in ['IN_PROGRESS', 'ENQUEUED']:
            accounting_export.status = 'ENQUEUED'
            accounting_export.save()

        last_export = False
        if accounting_exports.count() == index + 1:
            last_export = True

        chain.append('apps.business_central.exports.purchase_invoice.tasks.create_purchase_invoice', accounting_export, last_export)

    if chain.length() > 1:
        chain.run()
