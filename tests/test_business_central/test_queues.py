from datetime import datetime

from apps.accounting_exports.models import Error
from apps.business_central.exports.journal_entry.queues import (
    check_accounting_export_and_start_import
    as
    check_accounting_export_and_start_import_journal_entry
)
from apps.business_central.exports.purchase_invoice.queues import (
    check_accounting_export_and_start_import
    as
    check_accounting_export_and_start_import_purchase_invoice
)


def test_check_accounting_export_and_start_import_journal_entry(
    db,
    create_temp_workspace,
    add_fyle_credentials,
    create_export_settings,
    create_accounting_export_expenses,
    mocker
):
    """
    Test check_accounting_export_and_start_import for journal entry
    """
    accounting_export = create_accounting_export_expenses

    mocker.patch('apps.business_central.exports.journal_entry.tasks.create_journal_entry')
    mocker.patch('apps.fyle.helpers.sync_dimensions')
    mocker.patch('django_q.tasks.Chain.run')

    check_accounting_export_and_start_import_journal_entry(
        accounting_export.workspace_id,
        [accounting_export.id],
        False,
        0
    )

    accounting_export.refresh_from_db()

    assert accounting_export.status == 'ENQUEUED'
    assert accounting_export.type == 'JOURNAL_ENTRY'

    accounting_export.status = 'DONE'
    accounting_export.save()

    check_accounting_export_and_start_import_journal_entry(
        accounting_export.workspace_id,
        [accounting_export.id],
        False,
        0
    )

    accounting_export.refresh_from_db()

    assert accounting_export.status == 'ENQUEUED'
    assert accounting_export.type == 'JOURNAL_ENTRY'


def test_check_accounting_export_and_start_import_purchase_invoice(
    db,
    create_temp_workspace,
    add_fyle_credentials,
    create_export_settings,
    create_accounting_export_expenses,
    mocker
):
    """
    Test check_accounting_export_and_start_import for purchase invoice
    """
    accounting_export = create_accounting_export_expenses

    mocker.patch('apps.business_central.exports.purchase_invoice.tasks.create_purchase_invoice')
    mocker.patch('apps.fyle.helpers.sync_dimensions')
    mocker.patch('django_q.tasks.Chain.run')

    check_accounting_export_and_start_import_purchase_invoice(
        accounting_export.workspace_id,
        [accounting_export.id],
        False,
        0
    )

    accounting_export.refresh_from_db()

    assert accounting_export.status == 'ENQUEUED'
    assert accounting_export.type == 'PURCHASE_INVOICE'

    accounting_export.status = 'COMPLETE'
    accounting_export.save()

    check_accounting_export_and_start_import_purchase_invoice(
        accounting_export.workspace_id,
        [accounting_export.id],
        False,
        0
    )

    accounting_export.refresh_from_db()

    assert accounting_export.status == 'COMPLETE'
    assert accounting_export.type == 'PURCHASE_INVOICE'


def test_skipping_journal_entry(
    db,
    create_temp_workspace,
    add_fyle_credentials,
    create_export_settings,
    create_accounting_export_expenses,
    mocker
):
    """
    Test skipping for journal entry
    """

    workspace_id = 1
    accounting_export = create_accounting_export_expenses
    accounting_export.status = ''
    accounting_export.exported_at = None
    accounting_export.save()

    error = Error.objects.filter(workspace_id=workspace_id, accounting_export=accounting_export).delete()

    error = Error.objects.create(
        workspace_id=workspace_id,
        type='NETSUITE_ERROR',
        error_title='NetSuite System Error',
        error_detail='An error occured in a upsert request: Please enter value(s) for: Location',
        accounting_export=accounting_export,
        repetition_count=106
    )

    mocker.patch('apps.business_central.exports.journal_entry.tasks.create_journal_entry')
    mocker.patch('apps.fyle.helpers.sync_dimensions')
    mocker.patch('django_q.tasks.Chain.run')

    check_accounting_export_and_start_import_journal_entry(
        accounting_export.workspace_id,
        [accounting_export.id],
        True,
        1
    )

    accounting_export.refresh_from_db()

    assert accounting_export.status == ''
    assert accounting_export.type == 'JOURNAL_ENTRY'

    Error.objects.filter(id=error.id).update(updated_at=datetime(2024, 8, 20))

    check_accounting_export_and_start_import_journal_entry(
        accounting_export.workspace_id,
        [accounting_export.id],
        True,
        1
    )

    accounting_export.refresh_from_db()

    assert accounting_export.status == 'ENQUEUED'
    assert accounting_export.type == 'JOURNAL_ENTRY'


def test_skipping_purchase_invoice(
    db,
    create_temp_workspace,
    add_fyle_credentials,
    create_export_settings,
    create_accounting_export_expenses,
    mocker
):
    """
    Test skipping for purchase invoice
    """

    workspace_id = 1
    accounting_export = create_accounting_export_expenses
    accounting_export.status = ''
    accounting_export.exported_at = None
    accounting_export.save()

    error = Error.objects.filter(workspace_id=workspace_id, accounting_export=accounting_export).delete()

    error = Error.objects.create(
        workspace_id=workspace_id,
        type='NETSUITE_ERROR',
        error_title='NetSuite System Error',
        error_detail='An error occured in a upsert request: Please enter value(s) for: Location',
        accounting_export=accounting_export,
        repetition_count=106
    )

    mocker.patch('apps.business_central.exports.purchase_invoice.tasks.create_purchase_invoice')
    mocker.patch('apps.fyle.helpers.sync_dimensions')
    mocker.patch('django_q.tasks.Chain.run')

    check_accounting_export_and_start_import_purchase_invoice(
        accounting_export.workspace_id,
        [accounting_export.id],
        True,
        1
    )

    accounting_export.refresh_from_db()

    assert accounting_export.status == ''
    assert accounting_export.type == 'PURCHASE_INVOICE'

    Error.objects.filter(id=error.id).update(updated_at=datetime(2024, 8, 20))

    check_accounting_export_and_start_import_purchase_invoice(
        accounting_export.workspace_id,
        [accounting_export.id],
        True,
        1
    )

    accounting_export.refresh_from_db()

    assert accounting_export.status == 'ENQUEUED'
    assert accounting_export.type == 'PURCHASE_INVOICE'
