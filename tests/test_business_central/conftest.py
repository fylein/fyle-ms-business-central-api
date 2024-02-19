import pytest
from apps.accounting_exports.models import AccountingExport
from apps.workspaces.models import AdvancedSetting, ExportSetting
from apps.fyle.models import Expense
from fyle_accounting_mappings.models import (
    ExpenseAttribute,
    DestinationAttribute,
    EmployeeMapping,
    CategoryMapping,
    Mapping
)
from apps.business_central.models import JournalEntry, JournalEntryLineItems
from apps.business_central.models import PurchaseInvoice, PurchaseInvoiceLineitems
from apps.workspaces.models import Workspace

from .fixtures import data


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def create_export_settings():
    export_settings_data = data['export_settings']
    export_settings = ExportSetting.objects.create(**export_settings_data)

    return export_settings


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def add_advanced_settings():
    advanced_settings_data = data['advanced_setting']
    advanced_settings = AdvancedSetting.objects.create(**advanced_settings_data)

    return advanced_settings


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def create_expense_objects():
    workspace_id = 1
    expenses = data['expenses']
    expense_objects = Expense.create_expense_objects(expenses=expenses, workspace_id=workspace_id)

    return expense_objects


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def create_accounting_export_expenses(create_expense_objects):
    workspace_id = 1
    fund_source = 'PERSONAL'
    expense_objects = create_expense_objects
    AccountingExport.create_accounting_export(expense_objects=expense_objects, fund_source=fund_source, workspace_id=workspace_id)
    accounting_export = AccountingExport.objects.all().first()

    return accounting_export


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def create_expense_attribute():
    expense_attribute_data = data['employee_expense_attributes']
    expense_attribute_data['workspace'] = Workspace.objects.get(id=1)
    expense_attribute = ExpenseAttribute.objects.create(**expense_attribute_data)

    return expense_attribute


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def create_destination_attribute():
    destination_emp_data = data['employee_destination_attributes']
    destination_emp_data['workspace'] = Workspace.objects.get(id=1)
    DestinationAttribute.objects.create(**destination_emp_data)

    destination_vendor_data = data['vendor_destination_attributes']
    destination_vendor_data['workspace'] = Workspace.objects.get(id=1)
    DestinationAttribute.objects.create(**destination_vendor_data)


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def create_employee_mapping_with_employee(create_expense_attribute, create_destination_attribute):
    source_field_id = ExpenseAttribute.objects.get(source_id='source123')
    destination_field_id = DestinationAttribute.objects.get(destination_id='destination123')
    workspace = Workspace.objects.get(id=1)

    employee_employee_mapping = {
        'source_employee': source_field_id,
        'destination_employee': destination_field_id,
        'workspace': workspace,
    }

    EmployeeMapping.objects.create(**employee_employee_mapping)


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def create_employee_mapping_with_vendor(create_expense_attribute, create_destination_attribute):
    source_field_id = ExpenseAttribute.objects.get(source_id='source123')
    destination_field_id = DestinationAttribute.objects.get(destination_id='dest_vendor123')
    workspace = Workspace.objects.get(id=1)

    employee_vendor_mapping = {
        'source_employee': source_field_id,
        'destination_vendor': destination_field_id,
        'workspace': workspace,
    }

    EmployeeMapping.objects.create(**employee_vendor_mapping)


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def create_source_category_attribute():
    source_category_attribute_data = data['category_expense_attributes']
    source_category_attribute_data['workspace'] = Workspace.objects.get(id=1)
    source_category_attribute = ExpenseAttribute.objects.create(**source_category_attribute_data)

    return source_category_attribute


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def create_destination_category_attribute():
    destination_category_attribute_data = data['category_destination_attributes']
    destination_category_attribute_data['workspace'] = Workspace.objects.get(id=1)
    destination_category_attribute = DestinationAttribute.objects.create(**destination_category_attribute_data)

    return destination_category_attribute


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def create_category_mapping(create_source_category_attribute, create_destination_category_attribute):
    source_category = ExpenseAttribute.objects.get(source_id='src_category123')
    destination_category = DestinationAttribute.objects.get(destination_id='dest_category123')
    workspace = Workspace.objects.get(id=1)

    category_mapping = CategoryMapping.create_or_update_category_mapping(
        source_category_id=source_category.id,
        destination_account_id=destination_category.id,
        workspace=workspace
    )

    return category_mapping


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def create_journal_entry(
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

    JournalEntry.create_or_update_object(
        accounting_export=accounting_export,
        _=advanced_setting,
        export_settings=export_settings
    )

    return JournalEntry.objects.first()


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def create_journal_line_items(
    add_fyle_credentials,
    create_journal_entry,
    create_category_mapping
):
    workspace_id = 1
    export_settings = ExportSetting.objects.get(workspace_id=workspace_id)
    advanced_setting = AdvancedSetting.objects.get(workspace_id=workspace_id)
    accounting_export = AccountingExport.objects.get(workspace_id=workspace_id)

    journal_line_items = JournalEntryLineItems.create_or_update_object(
        accounting_export=accounting_export,
        advance_setting=advanced_setting,
        export_settings=export_settings
    )

    return journal_line_items


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def create_purchase_invoice(
    create_temp_workspace,
    create_export_settings,
    add_advanced_settings,
    create_employee_mapping_with_employee,
    create_accounting_export_expenses,
):
    workspace_id = 1
    export_settings = ExportSetting.objects.get(workspace_id=workspace_id)
    advanced_setting = AdvancedSetting.objects.get(workspace_id=workspace_id)
    accounting_export = AccountingExport.objects.get(workspace_id=workspace_id)

    PurchaseInvoice.create_or_update_object(
        accounting_export=accounting_export,
        _=advanced_setting,
        export_settings=export_settings
    )

    return PurchaseInvoice.objects.first()


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def create_purchase_invoice_line_items(
    add_fyle_credentials,
    create_purchase_invoice,
    create_category_mapping
):
    workspace_id = 1
    export_settings = ExportSetting.objects.get(workspace_id=workspace_id)
    advanced_setting = AdvancedSetting.objects.get(workspace_id=workspace_id)
    accounting_export = AccountingExport.objects.get(workspace_id=workspace_id)

    purchase_invoice_line_items = PurchaseInvoiceLineitems.create_or_update_object(
        accounting_export=accounting_export,
        advance_setting=advanced_setting,
        _=export_settings
    )

    return purchase_invoice_line_items


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def create_mapping_object(
    create_temp_workspace,
    create_expense_attribute,
    create_destination_attribute
):
    workspace_id = 1
    expense_attribute = ExpenseAttribute.objects.filter(workspace_id=workspace_id).first()
    destination_attribute = DestinationAttribute.objects.filter(workspace_id=workspace_id).first()
    workspace = Workspace.objects.get(id=workspace_id)

    mapping_object = Mapping.objects.create(
        source_type=expense_attribute.attribute_type,
        destination_type=destination_attribute.attribute_type,
        source=expense_attribute,
        destination=destination_attribute,
        workspace=workspace
    )

    return mapping_object
