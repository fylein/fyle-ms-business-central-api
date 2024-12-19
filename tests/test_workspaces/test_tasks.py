from apps.workspaces.tasks import (
    async_update_fyle_credentials,
    run_import_export,
    schedule_sync,
    export_to_business_central,
    async_create_admin_subcriptions
)
from apps.accounting_exports.models import AccountingExport, AccountingExportSummary
from apps.workspaces.models import BusinessCentralCredentials, FyleCredential, AdvancedSetting, ExportSetting
from django_q.models import Schedule
from django.conf import settings
from django.urls import reverse


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


def test_run_import_export_with_reimbursable_expense(
    db,
    mocker,
    create_temp_workspace,
    add_fyle_credentials,
    create_export_settings,
    add_advanced_settings,
    create_accounting_export_expenses
):
    workspace_id = 1
    accounting_export = AccountingExport.objects.get(workspace_id=workspace_id)

    advanced_settings = AdvancedSetting.objects.get(workspace_id=workspace_id)
    advanced_settings.interval_hours = 5
    advanced_settings.save()

    export_settings = ExportSetting.objects.get(workspace_id=workspace_id)
    export_settings.reimbursable_expenses_export_type = 'JOURNAL_ENTRY'
    export_settings.credit_card_expense_export_type = None
    export_settings.save()

    accounting_export.status = 'COMPLETE'
    accounting_export.fund_source = 'PERSONAL'
    accounting_export.type = 'FETCHING_REIMBURSABLE_EXPENSES'
    accounting_export.exported_at = None
    accounting_export.save()

    mocker.patch('apps.workspaces.tasks.queue_import_reimbursable_expenses')
    mock_export_journal_entry = mocker.patch('apps.business_central.exports.journal_entry.tasks.ExportJournalEntry')
    mocker.patch.object(
        mock_export_journal_entry.return_value,
        'trigger_export'
    )

    BusinessCentralCredentials.objects.create(
        workspace_id=workspace_id, is_expired=False, refresh_token='bsajkdbasjb'
    )

    run_import_export(workspace_id=workspace_id)

    accounting_summary = AccountingExportSummary.objects.get(workspace_id=workspace_id)

    accounting_export = AccountingExport.objects.get(
        workspace_id=workspace_id,
        type='FETCHING_REIMBURSABLE_EXPENSES'
    )

    assert accounting_export.status == 'COMPLETE'
    assert accounting_export.fund_source == 'PERSONAL'
    assert accounting_export.type == 'FETCHING_REIMBURSABLE_EXPENSES'
    assert accounting_summary.export_mode == 'MANUAL'
    assert accounting_summary.last_exported_at is not None


def test_run_import_export_with_credit_card_expenses(
    db,
    mocker,
    create_temp_workspace,
    add_fyle_credentials,
    create_export_settings,
    add_advanced_settings,
    create_accounting_export_expenses
):
    workspace_id = 1
    accounting_export = AccountingExport.objects.get(workspace_id=workspace_id)

    advanced_settings = AdvancedSetting.objects.get(workspace_id=workspace_id)
    advanced_settings.interval_hours = 5
    advanced_settings.save()

    export_settings = ExportSetting.objects.get(workspace_id=workspace_id)
    export_settings.reimbursable_expenses_export_type = None
    export_settings.credit_card_expense_export_type = 'JOURNAL_ENTRY'
    export_settings.save()

    accounting_export.status = 'COMPLETE'
    accounting_export.fund_source = 'CCC'
    accounting_export.type = 'FETCHING_CREDIT_CARD_EXPENSES'
    accounting_export.exported_at = None
    accounting_export.save()

    mocker.patch('apps.workspaces.tasks.queue_import_credit_card_expenses')
    mock_export_journal_entry = mocker.patch('apps.business_central.exports.journal_entry.tasks.ExportJournalEntry')
    mocker.patch.object(
        mock_export_journal_entry.return_value,
        'trigger_export'
    )

    BusinessCentralCredentials.objects.create(
        workspace_id=workspace_id, is_expired=False, refresh_token='bsajkdbasjb'
    )

    run_import_export(workspace_id=workspace_id, export_mode='AUTOMATIC')

    accounting_summary = AccountingExportSummary.objects.get(workspace_id=workspace_id)

    accounting_export = AccountingExport.objects.get(
        workspace_id=workspace_id,
        type='FETCHING_CREDIT_CARD_EXPENSES'
    )

    assert accounting_export.status == 'COMPLETE'
    assert accounting_export.fund_source == 'CCC'
    assert accounting_export.type == 'FETCHING_CREDIT_CARD_EXPENSES'
    assert accounting_summary.export_mode == 'AUTOMATIC'
    assert accounting_summary.last_exported_at is not None


def test_sync_schedule(
    db,
    mocker,
    create_temp_workspace,
    add_advanced_settings
):
    workspace_id = 1

    advance_settings = AdvancedSetting.objects.get(workspace_id=workspace_id)
    advance_settings.schedule_is_enabled = True
    advance_settings.save()

    advanced_settings = schedule_sync(
        workspace_id=workspace_id,
        schedule_enabled=True,
        hours=5,
        email_added=['test2@fyle.in', 'test2@fyle.in'],
        emails_selected=['test1@fyle.in']
    )

    schedule = Schedule.objects.filter(
        args=f'{workspace_id}',
        func='apps.workspaces.tasks.run_import_export'
    ).first()

    assert schedule is not None
    assert advanced_settings.schedule_is_enabled == True
    assert advanced_settings.emails_selected == ['test1@fyle.in']
    assert advanced_settings.interval_hours == 5


def test_sync_schedule_2(
    db,
    mocker,
    create_temp_workspace,
    add_advanced_settings
):
    workspace_id = 1

    advance_settings = AdvancedSetting.objects.get(workspace_id=workspace_id)
    advance_settings.schedule_is_enabled = True
    advance_settings.save()

    schedules = Schedule.objects.filter(
        args=f'{workspace_id}',
        func='apps.workspaces.tasks.run_import_export',
    )

    assert schedules.count() == 0

    advanced_settings = schedule_sync(
        workspace_id=workspace_id,
        schedule_enabled=False,
        hours=5,
        email_added=['test2@fyle.in', 'test2@fyle.in'],
        emails_selected=['test1@fyle.in']
    )

    schedules = Schedule.objects.filter(
        args=f'{workspace_id}',
        func='apps.workspaces.tasks.run_import_export',
    )

    assert schedules.count() == 0
    assert schedules.first() is None
    assert advanced_settings.schedule_is_enabled == False


def test_export_to_business_central_with_reimbursable_expense(
    db,
    mocker,
    create_temp_workspace,
    add_fyle_credentials,
    create_export_settings,
    add_advanced_settings,
    create_accounting_export_expenses
):
    workspace_id = 1
    accounting_export = AccountingExport.objects.get(workspace_id=workspace_id)

    advanced_settings = AdvancedSetting.objects.get(workspace_id=workspace_id)
    advanced_settings.interval_hours = 5
    advanced_settings.save()

    export_settings = ExportSetting.objects.get(workspace_id=workspace_id)
    export_settings.reimbursable_expenses_export_type = 'JOURNAL_ENTRY'
    export_settings.credit_card_expense_export_type = None
    export_settings.save()

    accounting_export.status = 'COMPLETE'
    accounting_export.fund_source = 'PERSONAL'
    accounting_export.exported_at = None
    accounting_export.save()

    mock_export_journal_entry = mocker.patch('apps.business_central.exports.journal_entry.tasks.ExportJournalEntry')
    mock_export_purchase_invoice = mocker.patch('apps.business_central.exports.purchase_invoice.tasks.ExportPurchaseInvoice')
    mocker.patch.object(
        mock_export_journal_entry.return_value,
        'trigger_export'
    )
    mocker.patch.object(
        mock_export_purchase_invoice.return_value,
        'trigger_export'
    )

    export_to_business_central(workspace_id=workspace_id)

    accounting_summary = AccountingExportSummary.objects.get(workspace_id=workspace_id)

    accounting_export = AccountingExport.objects.get(
        workspace_id=workspace_id,
    )

    assert accounting_export.status == 'COMPLETE'
    assert accounting_export.fund_source == 'PERSONAL'
    assert accounting_summary.export_mode == 'MANUAL'
    assert accounting_summary.last_exported_at is not None

    export_settings.reimbursable_expenses_export_type = 'PURCHASE_INVOICE'
    export_settings.save()

    export_to_business_central(workspace_id=workspace_id)

    accounting_summary = AccountingExportSummary.objects.get(workspace_id=workspace_id)

    accounting_export = AccountingExport.objects.get(workspace_id=workspace_id)

    assert accounting_export.status == 'COMPLETE'
    assert accounting_export.fund_source == 'PERSONAL'
    assert accounting_summary.export_mode == 'MANUAL'
    assert accounting_summary.last_exported_at is not None


def test_async_create_admin_subcriptions(
    db,
    mocker,
    create_temp_workspace,
    add_fyle_credentials
):
    mock_api = mocker.patch(
        'fyle.platform.apis.v1beta.admin.Subscriptions.post',
        return_value={}
    )
    workspace_id = 1
    async_create_admin_subcriptions(workspace_id=workspace_id)

    payload = {
        'is_enabled': True,
        'webhook_url': '{}/workspaces/{}/fyle/webhook_callback/'.format(settings.API_URL, workspace_id)
    }

    assert mock_api.once_called_with(payload)

    mock_api.side_effect = Exception('Error')
    try:
        async_create_admin_subcriptions(workspace_id=workspace_id)
    except Exception as e:
        assert str(e) == 'Error'


def test_async_create_admin_subcriptions_2(
    db,
    mocker,
    create_temp_workspace,
    add_fyle_credentials
):
    mock_api = mocker.patch(
        'fyle.platform.apis.v1beta.admin.Subscriptions.post',
        return_value={}
    )
    workspace_id = 1
    reverse('webhook-callback', kwargs={'workspace_id': workspace_id})

    payload = {
        'is_enabled': True,
        'webhook_url': '{}/workspaces/{}/fyle/webhook_callback/'.format(settings.API_URL, workspace_id)
    }

    assert mock_api.once_called_with(payload)

    mock_api.side_effect = Exception('Error')
    reverse('webhook-callback', kwargs={'workspace_id': workspace_id})


def test_run_import_export_with_no_bc_creds(db):
    workspace_id = 10
    response = run_import_export(workspace_id=workspace_id)

    assert response is None
