from apps.business_central.models import (
    JournalEntry,
    JournalEntryLineItems,
    PurchaseInvoice,
    PurchaseInvoiceLineitems
)
from apps.workspaces.models import AdvancedSetting, ExportSetting
from apps.accounting_exports.models import AccountingExport
from fyle_accounting_mappings.models import EmployeeMapping


def test_create_or_update_journal_entry_1(
    db,
    create_temp_workspace,
    create_export_settings,
    add_advanced_settings,
    create_accounting_export_expenses,
    create_employee_mapping_with_employee
):
    workspace_id = 1
    export_settings = ExportSetting.objects.get(workspace_id=workspace_id)
    advanced_setting = AdvancedSetting.objects.get(workspace_id=workspace_id)
    accounting_export = AccountingExport.objects.get(workspace_id=workspace_id)

    assert accounting_export.description.get('employee_email') == "ashwin.t@fyle.in"

    JournalEntry.create_or_update_object(
        accounting_export=accounting_export,
        _ = advanced_setting,
        export_settings=export_settings
    )

    journal_entry = JournalEntry.objects.first()
    assert journal_entry.accounting_export.workspace.id == 1
    assert journal_entry.amount == -50


def test_create_or_update_journal_entry_2(
    db,
    create_temp_workspace,
    create_export_settings,
    add_advanced_settings,
    create_accounting_export_expenses,
    create_employee_mapping_with_vendor
):
    workspace_id = 1
    export_settings = ExportSetting.objects.get(workspace_id=workspace_id)
    advanced_setting = AdvancedSetting.objects.get(workspace_id=workspace_id)
    accounting_export = AccountingExport.objects.get(workspace_id=workspace_id)

    assert accounting_export.description.get('employee_email') == "ashwin.t@fyle.in"

    export_settings.reimbursable_expenses_export_type = 'PURCHASE_INVOICE'
    export_settings.save()

    mapping = EmployeeMapping.objects.filter(
        source_employee__value=accounting_export.description.get('employee_email'),
        workspace_id=accounting_export.workspace_id
    ).first()

    assert mapping.destination_vendor.destination_id == "dest_vendor123"

    JournalEntry.create_or_update_object(
        accounting_export=accounting_export,
        _ = advanced_setting,
        export_settings=export_settings
    )

    journal_entry = JournalEntry.objects.first()
    assert journal_entry.accounting_export.workspace.id == 1
    assert journal_entry.amount == -50


def test_create_or_update_journal_entry_3(
    db,
    create_temp_workspace,
    create_export_settings,
    add_advanced_settings,
    create_accounting_export_expenses,
    create_employee_mapping_with_vendor
):
    workspace_id = 1
    export_settings = ExportSetting.objects.get(workspace_id=workspace_id)
    advanced_setting = AdvancedSetting.objects.get(workspace_id=workspace_id)
    accounting_export = AccountingExport.objects.get(workspace_id=workspace_id)

    assert accounting_export.description.get('employee_email') == "ashwin.t@fyle.in"

    export_settings.reimbursable_expenses_export_type = 'JOURNAL_ENTRY'
    export_settings.name_in_journal_entry = 'MERCHANT'
    export_settings.save()

    accounting_export.fund_source = 'CCC'
    accounting_export.save()

    mapping = EmployeeMapping.objects.filter(
        source_employee__value=accounting_export.description.get('employee_email'),
        workspace_id=accounting_export.workspace_id
    ).first()

    assert mapping.destination_vendor.destination_id == "dest_vendor123"

    JournalEntry.create_or_update_object(
        accounting_export=accounting_export,
        _ = advanced_setting,
        export_settings=export_settings
    )

    journal_entry = JournalEntry.objects.first()
    assert journal_entry.accounting_export.workspace.id == 1
    assert journal_entry.amount == -50


def test_create_or_update_journal_entry_line_items(
        db,
        create_temp_workspace,
        create_export_settings,
        add_advanced_settings,
        create_accounting_export_expenses,
        create_employee_mapping_with_employee,
        add_fyle_credentials,
        create_category_mapping
):
    workspace_id = 1

    export_settings = ExportSetting.objects.get(workspace_id=workspace_id)
    advanced_setting = AdvancedSetting.objects.get(workspace_id=workspace_id)
    accounting_export = AccountingExport.objects.get(workspace_id=workspace_id)

    JournalEntry.create_or_update_object(
        accounting_export=accounting_export,
        _ = advanced_setting,
        export_settings=export_settings
    )

    assert JournalEntry.objects.first().accounting_export.workspace.id == 1

    journal_line_items = JournalEntryLineItems.create_or_update_object(
        accounting_export=AccountingExport.objects.get(workspace_id=workspace_id),
        advance_setting=AdvancedSetting.objects.get(workspace_id=workspace_id),
        export_settings=ExportSetting.objects.get(workspace_id=workspace_id)
    )

    assert len(journal_line_items) == 1
    assert journal_line_items[0].journal_entry.accounting_export.workspace.id == 1
    assert journal_line_items[0].journal_entry.amount == -50


def test_create_or_update_purchase_invoice(
        db,
        create_temp_workspace,
        create_export_settings,
        add_advanced_settings,
        create_accounting_export_expenses,
        create_employee_mapping_with_employee
):
    workspace_id = 1

    purchase_invoice = PurchaseInvoice.create_or_update_object(
        accounting_export=AccountingExport.objects.get(workspace_id=workspace_id),
        _=AdvancedSetting.objects.get(workspace_id=workspace_id),
        export_settings=ExportSetting.objects.get(workspace_id=workspace_id)
    )

    assert purchase_invoice.accounting_export.workspace.id == 1
    assert purchase_invoice.amount == 50


def test_create_or_update_purchase_invoice_line_items(
        db,
        create_temp_workspace,
        create_export_settings,
        add_advanced_settings,
        create_accounting_export_expenses,
        create_employee_mapping_with_employee,
        add_fyle_credentials,
        create_category_mapping
):
    workspace_id = 1

    PurchaseInvoice.create_or_update_object(
        accounting_export=AccountingExport.objects.get(workspace_id=workspace_id),
        _=AdvancedSetting.objects.get(workspace_id=workspace_id),
        export_settings=ExportSetting.objects.get(workspace_id=workspace_id)
    )

    assert PurchaseInvoice.objects.first().accounting_export.workspace.id == 1

    purchase_invoice_line_items = PurchaseInvoiceLineitems.create_or_update_object(
        accounting_export=AccountingExport.objects.get(workspace_id=workspace_id),
        advance_setting=AdvancedSetting.objects.get(workspace_id=workspace_id),
        _=ExportSetting.objects.get(workspace_id=workspace_id)
    )

    assert len(purchase_invoice_line_items) == 1
    assert purchase_invoice_line_items[0].purchase_invoice.accounting_export.workspace.id == 1
    assert purchase_invoice_line_items[0].purchase_invoice.amount == 50
