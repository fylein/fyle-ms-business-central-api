import pytest

from apps.business_central.exports.helpers import (
    get_employee_expense_attribute,
    get_filtered_mapping,
    __validate_category_mapping,
    __validate_employee_mapping,
    validate_accounting_export,
    resolve_errors_for_exported_accounting_export,
    load_attachments
)

from fyle_accounting_mappings.models import (
    CategoryMapping,
    EmployeeMapping,
    ExpenseAttribute,
    Mapping
)

from apps.accounting_exports.models import AccountingExport, Error
from apps.business_central.utils import BusinessCentralConnector, BusinessCentralCredentials
from apps.fyle.models import Expense
from apps.workspaces.models import ExportSetting

from ms_business_central_api.exceptions import BulkError


def test_get_employee_expense_attribute(
    db,
    mocker,
    create_temp_workspace,
    create_expense_attribute
):
    workspace_id = 1
    value = 'ashwin.t@fyle.in'

    expense_attribute = ExpenseAttribute.objects.filter(workspace_id=workspace_id).first()

    expense_attribute_response = get_employee_expense_attribute(value=value, workspace_id=workspace_id)

    assert expense_attribute_response.value == expense_attribute.value
    assert expense_attribute_response.workspace_id == expense_attribute.workspace_id
    assert expense_attribute_response.attribute_type == expense_attribute.attribute_type
    assert expense_attribute_response.display_name == expense_attribute.display_name


def test_resolve_errors_for_exported_accounting_export(
    db,
    create_temp_workspace,
    create_export_settings,
    create_accounting_export_expenses,
):
    workspace_id = 1
    accounting_export = AccountingExport.objects.filter(workspace_id = workspace_id).first()
    expense_attribute = ExpenseAttribute.objects.filter(workspace_id=workspace_id).first()

    Error.objects.create(
        workspace_id=workspace_id,
        type='EMPLOYEE_MAPPING',
        accounting_export=accounting_export,
        expense_attribute=expense_attribute,
        is_resolved=False,
        error_title='Employee Mapping error',
        error_detail='Employee Mapping error detail'
    )

    resolve_errors_for_exported_accounting_export(accounting_export=accounting_export)

    error = Error.objects.filter(workspace_id=workspace_id).first()

    assert error.is_resolved == True
    assert error.error_title == 'Employee Mapping error'
    assert error.error_detail == 'Employee Mapping error detail'
    assert error.type == 'EMPLOYEE_MAPPING'


def test_load_attachments_1(
    db,
    mocker,
    create_temp_workspace,
    add_business_central_creds,
    add_fyle_credentials,
    create_export_settings,
    create_accounting_export_expenses
):
    workspace_id = 1

    expense = Expense.objects.filter(workspace_id=workspace_id).first()
    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()

    business_central_creds = BusinessCentralCredentials.objects.filter(workspace_id=workspace_id).first()
    business_central_creds.workspace.business_central_company_id = "Business_Company_Id"
    business_central_creds.save()

    dynamic_connection_mock = mocker.patch('dynamics.core.client.Dynamics')
    dynamic_connection_mock.return_value.refresh_token = 'Dummy_Token'
    platform_mock = mocker.patch('fyle_integrations_platform_connector.PlatformConnector')
    mock_generate_file_urls = mocker.patch.object(
        platform_mock.return_value.files,
        'bulk_generate_file_urls',
        return_value=[
            {
                'id':1,
                'data':'dummy'
            }
        ]
    )

    business_central_connection = BusinessCentralConnector(
        credentials_object=business_central_creds,
        workspace_id=workspace_id
    )

    mock_post_attachments = mocker.patch.object(business_central_connection, 'post_attachments')

    load_attachments(
        business_central_connection=business_central_connection,
        ref_id="Ref_Id",
        ref_type="Ref_Type",
        expense=expense,
        accounting_export=accounting_export
    )

    assert mock_post_attachments.call_count == 0
    assert mock_generate_file_urls.call_count == 0


def test_load_attachments_2(
    db,
    mocker,
    create_temp_workspace,
    add_business_central_creds,
    add_fyle_credentials,
    create_export_settings,
    create_accounting_export_expenses
):
    workspace_id = 1

    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()
    expense = Expense.objects.filter(workspace_id=workspace_id).first()

    expense.file_ids = [1, 2, 3]
    expense.save()

    business_central_creds = BusinessCentralCredentials.objects.filter(workspace_id=workspace_id).first()
    business_central_creds.workspace.business_central_company_id = "Business_Company_Id"
    business_central_creds.save()

    dynamic_connection_mock = mocker.patch('apps.business_central.utils.Dynamics')
    dynamic_connection_mock.return_value.refresh_token = 'Dummy_Token'
    platform_mock = mocker.patch('apps.business_central.exports.helpers.PlatformConnector')
    mock_generate_file_urls = mocker.patch.object(
        platform_mock.return_value.files,
        'bulk_generate_file_urls',
        return_value=[
            {
                'id':1,
                'data':'dummy'
            }
        ]
    )

    business_central_connection = BusinessCentralConnector(
        credentials_object=business_central_creds,
        workspace_id=workspace_id
    )

    assert business_central_creds.refresh_token == 'Dummy_Token'

    mock_post_attachments = mocker.patch.object(business_central_connection, 'post_attachments')

    load_attachments(
        business_central_connection=business_central_connection,
        ref_id="Ref_Id",
        ref_type="Ref_Type",
        expense=expense,
        accounting_export=accounting_export
    )

    assert mock_post_attachments.call_count == 1
    assert mock_generate_file_urls.call_count == 1


def test_load_attachments_3(
    db,
    mocker,
    create_temp_workspace,
    add_business_central_creds,
    add_fyle_credentials,
    create_export_settings,
    create_accounting_export_expenses
):
    workspace_id = 1

    expense = Expense.objects.filter(workspace_id=workspace_id).first()
    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()

    business_central_creds = BusinessCentralCredentials.objects.filter(workspace_id=workspace_id).first()
    business_central_creds.workspace.business_central_company_id = "Business_Company_Id"
    business_central_creds.save()

    dynamic_connection_mock = mocker.patch('apps.business_central.utils.Dynamics')
    dynamic_connection_mock.return_value.refresh_token = 'Dummy_Token'
    platform_mock = mocker.patch(
        'apps.business_central.exports.helpers.PlatformConnector',
        side_effect=Exception('Error')
    )

    business_central_connection = BusinessCentralConnector(
        credentials_object=business_central_creds,
        workspace_id=workspace_id
    )

    assert business_central_creds.refresh_token == 'Dummy_Token'

    with pytest.raises(Exception) as e:
        load_attachments(
            business_central_connection=business_central_connection,
            ref_id="Ref_Id",
            ref_type="Ref_Type",
            expense=expense,
            accounting_export=accounting_export
        )

        assert str(e.value) == 'Error'

    assert platform_mock.call_count == 1


def test_get_filtered_mapping(
    db,
    create_temp_workspace,
    create_mapping_object
):
    workspace_id = 1
    mapping = Mapping.objects.filter(workspace_id=workspace_id).first()

    filtered_mapping = get_filtered_mapping(
        source_field="EMPLOYEE",
        destination_type="EMPLOYEE",
        workspace_id=workspace_id,
        source_id="source123",
        source_value="ashwin.t@fyle.in"
    )

    assert filtered_mapping.source_type == mapping.source_type
    assert filtered_mapping.destination_type == mapping.destination_type
    assert filtered_mapping.workspace_id == mapping.workspace_id
    assert filtered_mapping.source.source_id == mapping.source.source_id
    assert filtered_mapping.source.value == mapping.source.value


def test_validate_employee_mapping_1(
    db,
    create_temp_workspace,
    create_employee_mapping_with_employee,
    create_export_settings,
    create_accounting_export_expenses
):
    workspace_id = 1
    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()
    export_settings = ExportSetting.objects.filter(workspace_id=workspace_id).first()

    bulk_errors = __validate_employee_mapping(
        accounting_export=accounting_export,
        export_settings=export_settings
    )

    employee_mapping = EmployeeMapping.objects.filter(workspace_id=workspace_id).first()

    assert employee_mapping.source_employee.source_id == 'source123'
    assert len(bulk_errors) == 0


def test_validate_employee_mapping_2(
    db,
    create_temp_workspace,
    create_export_settings,
    create_accounting_export_expenses
):
    workspace_id = 1
    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()
    export_settings = ExportSetting.objects.filter(workspace_id=workspace_id).first()

    bulk_errors = __validate_employee_mapping(
        accounting_export=accounting_export,
        export_settings=export_settings
    )

    assert len(bulk_errors) == 1
    assert bulk_errors[0]['value'] == 'ashwin.t@fyle.in'
    assert bulk_errors[0]['type'] == 'Employee Mapping'
    assert bulk_errors[0]['message'] == 'Employee Mapping not found'


def test_validate_employee_mapping_3(
    db,
    create_temp_workspace,
    create_export_settings,
    create_accounting_export_expenses,
    create_employee_mapping_with_employee
):
    workspace_id = 1
    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()
    export_settings = ExportSetting.objects.filter(workspace_id=workspace_id).first()
    employee_mapping = EmployeeMapping.objects.filter(workspace_id=workspace_id).first()

    employee_mapping.destination_employee = None
    employee_mapping.save()

    bulk_errors = __validate_employee_mapping(
        accounting_export=accounting_export,
        export_settings=export_settings
    )

    error = Error.objects.filter(workspace_id=workspace_id).first()

    assert len(bulk_errors) == 1
    assert bulk_errors[0]['value'] == 'ashwin.t@fyle.in'
    assert bulk_errors[0]['type'] == 'Employee Mapping'
    assert bulk_errors[0]['message'] == 'Employee Mapping not found'

    assert error.type == 'EMPLOYEE_MAPPING'
    assert error.error_detail == 'Employee mapping is missing'
    assert error.is_resolved == False


def test_validate_employee_mapping_4(
    db,
    create_temp_workspace,
    create_export_settings,
    create_accounting_export_expenses,
    create_employee_mapping_with_vendor
):
    workspace_id = 1
    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()
    export_settings = ExportSetting.objects.filter(workspace_id=workspace_id).first()

    export_settings.employee_field_mapping = 'VENDOR'
    export_settings.save()

    bulk_errors = __validate_employee_mapping(
        accounting_export=accounting_export,
        export_settings=export_settings
    )

    employee_mapping = EmployeeMapping.objects.filter(workspace_id=workspace_id).first()

    assert employee_mapping.source_employee.source_id == 'source123'
    assert len(bulk_errors) == 0


def test_validate_category_mapping_1(
    db,
    create_temp_workspace,
    create_category_mapping,
    create_export_settings,
    create_accounting_export_expenses
):
    workspace_id = 1
    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()

    bulk_errors = __validate_category_mapping(accounting_export)

    category_mapping = CategoryMapping.objects.filter(workspace_id=workspace_id).first()

    assert category_mapping.source_category.attribute_type == 'CATEGORY'
    assert len(bulk_errors) == 0


def test_validate_category_mapping_2(
    db,
    create_temp_workspace,
    create_export_settings,
    create_accounting_export_expenses,
    create_category_mapping
):
    workspace_id = 1
    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()

    category_mapping = CategoryMapping.objects.filter(workspace_id=workspace_id).first()
    category_mapping.delete()

    assert accounting_export.expenses.first().category == 'Food'

    bulk_errors = __validate_category_mapping(accounting_export)

    error = Error.objects.filter(workspace_id=workspace_id).first()

    assert len(bulk_errors) == 1
    assert bulk_errors[0]['value'] == 'Food'
    assert bulk_errors[0]['type'] == 'Category Mapping'
    assert bulk_errors[0]['message'] == 'Category Mapping not found'

    assert error.type == 'CATEGORY_MAPPING'
    assert error.error_detail == 'Category mapping is missing'
    assert error.is_resolved == False


def test_validate_accounting_export(
    db,
    mocker,
    create_temp_workspace,
    create_export_settings,
    create_accounting_export_expenses
):
    workspace_id = 1
    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()
    export_settings = ExportSetting.objects.filter(workspace_id=workspace_id).first()

    mocker.patch(
        'apps.business_central.exports.helpers.__validate_employee_mapping',
        return_value={
            'row': 0,
            'id': 'Random Id',
            'error': 'Dummy Error',
            'type': 'Employee Mapping',
        }
    )
    mocker.patch(
        'apps.business_central.exports.helpers.__validate_category_mapping',
        return_value={
            'row': 0,
            'id': 'Random Id',
            'error': 'Dummy Error',
            'type': 'Category Mapping',
        }
    )

    with pytest.raises(BulkError) as e:
        validate_accounting_export(
            accounting_export=accounting_export,
            export_settings=export_settings
        )

        assert len(e.value.response) == 2
        assert e.value.response[0]['type'] == 'Employee Mapping'
        assert e.value.response[1]['type'] == 'Category Mapping'
