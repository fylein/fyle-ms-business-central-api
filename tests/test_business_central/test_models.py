import pytest
from fyle_accounting_mappings.models import EmployeeMapping, ExpenseAttribute, Mapping, MappingSetting

from apps.accounting_exports.models import AccountingExport, Expense
from apps.business_central.exports.accounting_export import AccountingDataExporter
from apps.business_central.models import JournalEntry, JournalEntryLineItems, PurchaseInvoice, PurchaseInvoiceLineitems
from apps.workspaces.models import AdvancedSetting, ExportSetting


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
    assert journal_entry.amount == 50


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
    assert journal_entry.amount == 50


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
    assert journal_entry.amount == 50


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
    assert journal_line_items[0].journal_entry.amount == 50


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


def test_accounting_data_exporter_1():
    workspace_id = 1
    accounting_data_exporter = AccountingDataExporter()

    with pytest.raises(NotImplementedError):
        accounting_data_exporter.post(
            workspace_id=workspace_id,
            body="Random body",
            lineitems="Random lineitems"
        )

    assert True


def test_accounting_data_exporter_2(
    db,
    mocker,
    create_temp_workspace,
    create_export_settings,
    add_advanced_settings,
    create_accounting_export_expenses,
    create_employee_mapping_with_employee,
    create_category_mapping
):
    workspace_id = 1

    accounting_export = AccountingExport.objects.get(workspace_id=workspace_id)

    accounting_export.status = 'ENQUEUED'
    accounting_export.save()

    accounting_data_exporter = AccountingDataExporter()

    mock_body_model = mocker.patch.object(accounting_data_exporter, 'body_model')
    mock_lineitem_model = mocker.patch.object(accounting_data_exporter, 'lineitem_model')

    mocker.patch.object(mock_body_model, 'create_or_update_object')
    mocker.patch.object(mock_lineitem_model, 'create_or_update_object')

    with pytest.raises(NotImplementedError):
        accounting_data_exporter.create_business_central_object(
            accounting_export=accounting_export
        )

    assert accounting_export.status == 'IN_PROGRESS'
    assert mock_body_model.create_or_update_object.call_count == 1
    assert mock_lineitem_model.create_or_update_object.call_count == 1


def test_accounting_data_exporter_3(
    db,
    mocker,
    create_temp_workspace,
    create_export_settings,
    add_advanced_settings,
    create_accounting_export_expenses,
    create_employee_mapping_with_employee,
    create_category_mapping
):
    workspace_id = 1

    accounting_export = AccountingExport.objects.get(workspace_id=workspace_id)

    accounting_export.status = 'ENQUEUED'
    accounting_export.save()

    accounting_data_exporter = AccountingDataExporter()

    mock_body_model = mocker.patch.object(accounting_data_exporter, 'body_model')
    mock_lineitem_model = mocker.patch.object(accounting_data_exporter, 'lineitem_model')

    mock_post = mocker.patch.object(accounting_data_exporter, 'post', return_value='Random response')

    mocker.patch.object(mock_body_model, 'create_or_update_object')
    mocker.patch.object(mock_lineitem_model, 'create_or_update_object')

    accounting_data_exporter.create_business_central_object(
        accounting_export=accounting_export
    )

    assert accounting_export.status == 'COMPLETE'
    assert mock_body_model.create_or_update_object.call_count == 1
    assert mock_lineitem_model.create_or_update_object.call_count == 1
    assert mock_post.call_count == 1

    assert accounting_export.detail == 'Random response'
    assert accounting_export.export_url == 'https://businesscentral.dynamics.com/'
    assert accounting_export.business_central_errors is None


def test_accounting_data_exporter_4(
    db,
    mocker,
    create_temp_workspace,
    create_export_settings,
    add_advanced_settings,
    create_accounting_export_expenses,
    create_employee_mapping_with_employee,
    create_category_mapping
):
    workspace_id = 1

    accounting_export = AccountingExport.objects.get(workspace_id=workspace_id)

    accounting_export.status = 'COMPLETE'
    accounting_export.save()

    accounting_data_exporter = AccountingDataExporter()

    mock_body_model = mocker.patch.object(accounting_data_exporter, 'body_model')
    mock_lineitem_model = mocker.patch.object(accounting_data_exporter, 'lineitem_model')
    mock_post = mocker.patch.object(accounting_data_exporter, 'post', return_value='Random response')

    mocker.patch.object(mock_body_model, 'create_or_update_object')
    mocker.patch.object(mock_lineitem_model, 'create_or_update_object')

    accounting_data_exporter.create_business_central_object(
        accounting_export=accounting_export
    )

    assert accounting_export.status == 'COMPLETE'
    assert mock_body_model.create_or_update_object.call_count == 0
    assert mock_lineitem_model.create_or_update_object.call_count == 0
    assert mock_post.call_count == 0


def test_base_model_get_invoice_date(
    db,
    create_temp_workspace,
    create_journal_entry
):
    workspace_id = 1

    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()
    base_model = JournalEntry

    accounting_export.description = {"spent_at": "2023-04-01T00:00:00"}
    return_value = base_model.get_invoice_date(accounting_export)
    assert return_value == "2023-04-01T00:00:00"

    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()
    accounting_export.description = {"approved_at": "2023-04-01T00:00:00"}
    accounting_export.save()
    return_value = base_model.get_invoice_date(accounting_export=accounting_export)
    assert return_value == "2023-04-01T00:00:00"

    accounting_export.description = {"verified_at": "2023-04-01T00:00:00"}
    return_value = base_model.get_invoice_date(accounting_export=accounting_export)
    assert return_value == "2023-04-01T00:00:00"

    accounting_export.description = {"last_spent_at": "2023-04-01T00:00:00"}
    return_value = base_model.get_invoice_date(accounting_export=accounting_export)
    assert return_value == "2023-04-01T00:00:00"

    accounting_export.description = {"posted_at": "2023-04-01T00:00:00"}
    return_value = base_model.get_invoice_date(accounting_export=accounting_export)
    assert return_value == "2023-04-01T00:00:00"


def test_base_model_get_location_id_1(
    db,
    create_mapping_object,
    create_export_settings,
    create_accounting_export_expenses,
    create_mapping_settings
):
    workspace_id = 1
    base_model = JournalEntry

    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()
    expenses = Expense.objects.filter(workspace_id=workspace_id).first()

    location_id = base_model.get_location_id(accounting_export, expenses)

    assert location_id is None


def test_base_model_get_location_id_2(
    db,
    create_mapping_object,
    create_export_settings,
    create_accounting_export_expenses,
    create_mapping_settings
):
    workspace_id = 1
    base_model = JournalEntry

    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()
    expenses = Expense.objects.filter(workspace_id=workspace_id).first()
    expense_attribute = ExpenseAttribute.objects.filter(workspace_id=workspace_id).first()
    expenses.project = 'ashwin.t@fyle.in'
    expenses.save()

    mapping_setting = MappingSetting.objects.filter(
        workspace_id=workspace_id,
        destination_field='LOCATION'
    ).first()

    mapping = Mapping.objects.filter(
        workspace_id=workspace_id,
    ).first()

    mapping_setting.source_field = 'PROJECT'
    mapping_setting.save()

    mapping.source_type = 'PROJECT'
    mapping.destination_type = 'LOCATION'
    mapping.save()

    location_id = base_model.get_location_id(accounting_export, expenses)
    assert location_id == mapping.destination.destination_id

    mapping_setting.source_field = 'COST_CENTER'
    mapping_setting.save()

    mapping.source_type = 'COST_CENTER'
    expense_attribute.value = 'Marketing'
    expense_attribute.save()
    mapping.source = expense_attribute
    mapping.save()

    location_id = base_model.get_location_id(accounting_export, expenses)
    assert location_id == mapping.destination.destination_id

    mapping_setting.source_field = 'CUSTOM'
    mapping_setting.save()

    mapping.source_type = 'CUSTOM'
    expense_attribute.attribute_type = 'CUSTOM'
    expense_attribute.display_name = 'CUSTOM'
    expense_attribute.value = 'Ashwin'
    expense_attribute.save()
    mapping.source = expense_attribute
    mapping.save()

    expenses.custom_properties = {
        'CUSTOM': 'Ashwin'
    }
    expenses.save()

    location_id = base_model.get_location_id(accounting_export, expenses)
    assert location_id == mapping.destination.destination_id


def test_get_expense_purpose(
    db,
    create_temp_workspace,
    create_expense_objects,
    add_advanced_settings
):
    workspace_id = 1
    base_model = JournalEntry
    category = 'Food'

    line_item = Expense.objects.filter(workspace_id=workspace_id).first()
    advanced_settings = AdvancedSetting.objects.filter(workspace_id=workspace_id).first()

    return_value = base_model.get_expense_purpose(line_item, category, advanced_settings)
    assert return_value == 'Food - ashwin.t@fyle.in'


def test_get_expense_comment(
    db,
    create_temp_workspace,
    create_expense_objects,
    add_advanced_settings,
    add_fyle_credentials
):
    workspace_id = 1
    base_model = JournalEntry
    category = 'Food'

    line_item = Expense.objects.filter(workspace_id=workspace_id).first()
    advanced_settings = AdvancedSetting.objects.filter(workspace_id=workspace_id).first()

    return_value = base_model.get_expense_comment(
        workspace_id=workspace_id,
        lineitem=line_item,
        category=category,
        advance_setting=advanced_settings
    )
    assert return_value == 'Food - ashwin.t@fyle.in'
