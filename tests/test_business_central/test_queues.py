import pytest

from apps.business_central.exports.journal_entry.queues import (
    check_accounting_export_and_start_import
    as
    check_accounting_export_and_start_import_journal_entry
)
from apps.business_central.exports.journal_entry.tasks import create_journal_entry
from apps.business_central.exports.purchase_invoice.queues import (
    check_accounting_export_and_start_import
    as
    check_accounting_export_and_start_import_purchase_invoice
)
from apps.business_central.exports.purchase_invoice.tasks import create_purchase_invoice


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

    check_accounting_export_and_start_import_journal_entry(
        accounting_export.workspace_id,
        [accounting_export.id]
    )

    accounting_export.refresh_from_db()

    assert accounting_export.status == 'ENQUEUED'
    assert accounting_export.type == 'JOURNAL_ENTRY'
    assert accounting_export.exported_at is None

    with pytest.raises(AttributeError):
        mocker.patch('apps.fyle.helpers.sync_dimensions')

        accounting_export.status = 'COMPLETE'
        accounting_export.save()

        check_accounting_export_and_start_import_journal_entry(
            accounting_export.workspace_id,
            [accounting_export.id]
        )

        accounting_export.refresh_from_db()

        assert accounting_export.status == 'ENQUEUED'
        assert accounting_export.type == 'JOURNAL_ENTRY'
        assert accounting_export.exported_at is None

        assert create_journal_entry.call_count == 1


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

    check_accounting_export_and_start_import_purchase_invoice(
        accounting_export.workspace_id,
        [accounting_export.id]
    )

    accounting_export.refresh_from_db()

    assert accounting_export.status == 'ENQUEUED'
    assert accounting_export.type == 'PURCHASE_INVOICE'
    assert accounting_export.exported_at is None

    with pytest.raises(AttributeError):
        mocker.patch('apps.fyle.helpers.sync_dimensions')

        accounting_export.status = 'COMPLETE'
        accounting_export.save()

        check_accounting_export_and_start_import_purchase_invoice(
            accounting_export.workspace_id,
            [accounting_export.id]
        )

        accounting_export.refresh_from_db()

        assert accounting_export.status == 'ENQUEUED'
        assert accounting_export.type == 'PURCHASE_INVOICE'
        assert accounting_export.exported_at is None

        assert create_purchase_invoice.call_count == 1
