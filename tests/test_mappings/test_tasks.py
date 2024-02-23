from apps.mappings.tasks import (
    sync_business_central_attributes,
    get_mapped_attributes_ids,
    resolve_expense_attribute_errors,
    async_auto_map_employees
)
from fyle_accounting_mappings.models import ExpenseAttribute
from fyle.platform.exceptions import InvalidTokenError
from apps.accounting_exports.models import Error, AccountingExport


def test_sync_business_central_attributes(
    db,
    mocker,
    create_temp_workspace,
    add_business_central_creds
):
    workspace_id = 1

    def test():
        pass

    mock_connector = mocker.patch('apps.mappings.tasks.BusinessCentralConnector')
    mocker.patch.object(
        mock_connector.return_value,
        'sync_accounts',
        return_value=test
    )
    mocker.patch.object(
        mock_connector.return_value,
        'sync_companies',
        return_value=test
    )
    mocker.patch.object(
        mock_connector.return_value,
        'sync_locations',
        return_value=test
    )
    mocker.patch.object(
        mock_connector.return_value,
        'sync_employees',
        return_value=test
    )
    mocker.patch.object(
        mock_connector.return_value,
        'sync_vendors',
        return_value=test
    )

    sync_business_central_attributes('ACCOUNT', workspace_id)
    sync_business_central_attributes('COMPANY', workspace_id)
    sync_business_central_attributes('LOCATION', workspace_id)
    sync_business_central_attributes('EMPLOYEE', workspace_id)
    sync_business_central_attributes('VENDOR', workspace_id)

    assert True


def test_get_mapped_attributes_ids(
    db,
    create_temp_workspace,
    create_employee_mapping_with_employee,
    create_employee_mapping_with_vendor
):
    source_attribute_type = 'EMPLOYEE'
    destination_attribute_type = 'EMPLOYEE'

    expense_attribute = ExpenseAttribute.objects.get(source_id='source123')
    errored_attribute_ids = [expense_attribute.id]

    mapped_attribute_ids = get_mapped_attributes_ids(
        source_attribute_type,
        destination_attribute_type,
        errored_attribute_ids
    )

    assert len(mapped_attribute_ids) == 1
    assert expense_attribute.id in mapped_attribute_ids

    source_attribute_type = 'EMPLOYEE'
    destination_attribute_type = 'VENDOR'

    mapped_attribute_ids = get_mapped_attributes_ids(
        source_attribute_type,
        destination_attribute_type,
        errored_attribute_ids
    )

    assert len(mapped_attribute_ids) == 1
    assert expense_attribute.id in mapped_attribute_ids


def test_resolve_expense_attribute_errors(
    db,
    mocker,
    create_temp_workspace,
    create_export_settings,
    create_accounting_export_expenses,
    create_employee_mapping_with_employee,
):
    workspace_id = 1

    Error.objects.create(
        type='EMPLOYEE_MAPPING',
        expense_attribute=ExpenseAttribute.objects.get(source_id='source123'),
        accounting_export=AccountingExport.objects.get(workspace_id=workspace_id),
        workspace_id=workspace_id,
        is_resolved=False,
        error_title='Employee Mapping Error',
        error_detail='Employee Mapping Error Detail'
    )

    resolve_expense_attribute_errors(
        source_attribute_type='EMPLOYEE',
        destination_attribute_type='EMPLOYEE',
        workspace_id=workspace_id
    )

    error = Error.objects.get(workspace_id=workspace_id)
    assert error.is_resolved == True


def test_async_auto_map_employees(
    db,
    mocker,
    create_temp_workspace,
    create_export_settings,
    add_fyle_credentials,
    add_business_central_creds,
    create_accounting_export_expenses,
    create_employee_mapping_with_employee,
):
    workspace_id = 1

    mock_platform = mocker.patch('apps.mappings.tasks.PlatformConnector')
    mock_business_central = mocker.patch('apps.mappings.tasks.BusinessCentralConnector')
    mock_employee_map_helper = mocker.patch('apps.mappings.tasks.EmployeesAutoMappingHelper')

    mocker.patch.object(
        mock_platform.return_value.employees,
        'sync'
    )
    mocker.patch.object(
        mock_business_central.return_value,
        'sync_employees'
    )
    mocker.patch.object(
        mock_business_central.return_value,
        'sync_vendors'
    )
    mocker.patch.object(
        mock_employee_map_helper.return_value,
        'reimburse_mapping'
    )

    async_auto_map_employees(workspace_id)
    assert True


def test_async_auto_map_employees_error1(
    db,
    mocker,
    create_temp_workspace,
    create_export_settings,
    add_fyle_credentials,
    add_business_central_creds,
):
    workspace_id = 1

    with mocker.patch(
        'apps.mappings.tasks.PlatformConnector',
        side_effect=InvalidTokenError('Invalid Token for fyle')
    ):
        try:
            async_auto_map_employees(workspace_id)
        except InvalidTokenError as e:
            assert str(e) == 'Invalid Token for fyle'

    mocker.patch('apps.mappings.tasks.PlatformConnector')

    with mocker.patch(
        'apps.mappings.tasks.BusinessCentralConnector',
        side_effect=InvalidTokenError(f'Invalid Token or Sage Intacct Credentials does not exist - {workspace_id}')
    ):
        try:
            async_auto_map_employees(workspace_id)
        except InvalidTokenError as e:
            assert str(e) == 'Invalid Token or Sage Intacct Credentials does not exist - 1'
