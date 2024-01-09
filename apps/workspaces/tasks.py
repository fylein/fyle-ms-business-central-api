import logging
from datetime import datetime, timedelta
from typing import List

from django_q.models import Schedule

from apps.accounting_exports.models import AccountingExport, AccountingExportSummary
from apps.business_central.exports.journal_entry.tasks import ExportJournalEntry
from apps.fyle.queue import queue_import_credit_card_expenses, queue_import_reimbursable_expenses
from apps.workspaces.models import AdvancedSetting, ExportSetting

logger = logging.getLogger(__name__)


def run_import_export(workspace_id: int, export_mode = None):
    """
    Run process to export to business central

    :param workspace_id: Workspace id
    """

    export_settings = ExportSetting.objects.get(workspace_id=workspace_id)
    advance_settings = AdvancedSetting.objects.get(workspace_id=workspace_id)
    accounting_summary, _ = AccountingExportSummary.objects.update_or_create(
        workspace_id=workspace_id
    )

    last_exported_at = datetime.now()
    is_expenses_exported = False

    export_map = {
        'JOURNAL_ENTRY': ExportJournalEntry()
    }

    # For Reimbursable Expenses
    if export_settings.reimbursable_expenses_export_type:
        queue_import_reimbursable_expenses(workspace_id=workspace_id,  synchronous=True)
        accounting_export = AccountingExport.objects.get(
            workspace_id=workspace_id,
            type='FETCHING_REIMBURSABLE_EXPENSES'
        )

        if accounting_export.status == 'COMPLETE':
            accounting_export_ids = AccountingExport.objects.filter(
                fund_source='PERSONAL', exported_at__isnull=True).values_list('id', flat=True)

            if len(accounting_export_ids):
                is_expenses_exported = True
                export = export_map[export_settings.reimbursable_expenses_export_type]
                export.trigger_export(workspace_id=workspace_id, accounting_export_ids=accounting_export_ids)

    # For Credit Card Expenses
    if export_settings.credit_card_expense_export_type:
        queue_import_credit_card_expenses(workspace_id=workspace_id, synchronous=True)
        accounting_export = AccountingExport.objects.get(
            workspace_id=workspace_id,
            type='FETCHING_CREDIT_CARD_EXPENSES'
        )
        if accounting_export.status == 'COMPLETE':
            accounting_export_ids = AccountingExport.objects.filter(
                fund_source='CCC', exported_at__isnull=True).values_list('id', flat=True)

            if len(accounting_export_ids):
                is_expenses_exported = True
                export = export_map[export_settings.credit_card_expense_export_type]
                export.trigger_export(workspace_id=workspace_id, accounting_export_ids=accounting_export_ids)

    if is_expenses_exported:
        accounting_summary.last_exported_at = last_exported_at
        accounting_summary.export_mode = export_mode or 'MANUAL'

        if advance_settings:
            accounting_summary.next_export_at = last_exported_at + timedelta(hours=24)

        accounting_summary.save()


def schedule_sync(workspace_id: int, schedule_enabled: bool, hours: int, email_added: List, emails_selected: List):

    advance_settings = AdvancedSetting.objects.get(workspace_id=workspace_id)

    if advance_settings.schedule_is_enabled:
        advance_settings.schedule_is_enabled = schedule_enabled
        advance_settings.start_datetime = datetime.now()
        advance_settings.interval_hours = hours
        advance_settings.emails_selected = emails_selected

        if email_added:
            advance_settings.emails_added = email_added

        # create next run by adding hours to current time
        next_run = datetime.now() + timedelta(hours=hours)

        schedule, _ = Schedule.objects.update_or_create(
            func='apps.workspaces.tasks.run_import_export',
            args='{}'.format(workspace_id),
            defaults={
                'schedule_type': Schedule.MINUTES,
                'minutes': hours * 60,
                'next_run': next_run
            }
        )

        advance_settings.schedule = schedule
        advance_settings.save()

    elif not schedule_enabled and advance_settings.schedule_is_enabled:
        schedule = advance_settings.schedule
        advance_settings.enabled = schedule_enabled
        advance_settings.schedule = None
        advance_settings.save()
        schedule.delete()

    return advance_settings


def export_to_business_central(workspace_id: int):
    """
    Function to export expenses to Business Central
    """
    # Retrieve export settings for the given workspace
    export_settings = ExportSetting.objects.get(workspace_id=workspace_id)

    # Update or create an AccountingExportSummary for the workspace
    accounting_summary, _ = AccountingExportSummary.objects.update_or_create(workspace_id=workspace_id)

    # Set the timestamp for the last export
    last_exported_at = datetime.now()

    # Flag to track if expenses are exported
    is_expenses_exported = False

    # Dictionary mapping export types to their corresponding export classes
    export_map = {
        'JOURNAL_ENTRY': ExportJournalEntry()
    }

    # Check and export reimbursable expenses if configured
    if export_settings.reimbursable_expenses_export_type:
        # Get IDs of unreexported accounting exports for personal fund source
        accounting_export_ids = AccountingExport.objects.filter(
            fund_source='PERSONAL', exported_at__isnull=True).values_list('id', flat=True)

        if len(accounting_export_ids):
            # Set the flag indicating expenses are exported
            is_expenses_exported = True
            # Get the appropriate export class and trigger the export
            export = export_map[export_settings.reimbursable_expenses_export_type]
            export.trigger_export(workspace_id=workspace_id, accounting_export_ids=accounting_export_ids)

    # Check and export credit card expenses if configured
    if export_settings.credit_card_expense_export_type:
        # Get IDs of unreexported accounting exports for credit card fund source
        accounting_export_ids = AccountingExport.objects.filter(
            fund_source='CCC', exported_at__isnull=True).values_list('id', flat=True)

        if len(accounting_export_ids):
            # Set the flag indicating expenses are exported
            is_expenses_exported = True
            # Get the appropriate export class and trigger the export
            export = export_map[export_settings.credit_card_expense_export_type]
            export.trigger_export(workspace_id=workspace_id, accounting_export_ids=accounting_export_ids)

    # Update the accounting summary if expenses are exported
    if is_expenses_exported:
        accounting_summary.last_exported_at = last_exported_at
        accounting_summary.export_mode = 'MANUAL'
        accounting_summary.save()