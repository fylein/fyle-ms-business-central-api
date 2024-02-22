from dynamics.exceptions.dynamics_exceptions import InvalidTokenError, WrongParamsError

from apps.business_central.exceptions import (
    handle_business_central_exceptions,
    handle_business_central_error
)
from apps.accounting_exports.models import AccountingExport, Error
from apps.workspaces.models import BusinessCentralCredentials, FyleCredential
from ms_business_central_api.exceptions import BulkError


def test_handle_business_central_error(
    db,
    create_temp_workspace,
    create_export_settings,
    create_accounting_export_expenses,
):
    workspace_id = 1
    export_type = 'Journal Entry'
    exception = WrongParamsError(response = 'Error', msg = 'Error')

    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()

    handle_business_central_error(exception, accounting_export, export_type)

    error = Error.objects.filter(workspace_id=workspace_id, accounting_export=accounting_export).first()
    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()

    assert accounting_export.status == 'FAILED'
    assert accounting_export.detail == None

    assert error.error_title == 'Failed to create Journal Entry'
    assert error.type == 'BUSINESS_CENTRAL_ERROR'
    assert error.error_detail == 'Error'
    assert error.is_resolved == False


def test_handle_business_central_exceptions(
    db,
    mocker,
    create_temp_workspace,
    create_export_settings,
    create_accounting_export_expenses,
    add_accounting_export_summary,
    add_business_central_creds

):
    workspace_id = 1
    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()

    @handle_business_central_exceptions()
    def test_func(accounting_export):
        raise FyleCredential.DoesNotExist('Fyle credentials not found')

    test_func(accounting_export)

    assert accounting_export.status == 'FAILED'
    assert accounting_export.detail == {'message': 'Fyle credentials do not exist in workspace'}

    @handle_business_central_exceptions()
    def test_func(accounting_export):
        raise BusinessCentralCredentials.DoesNotExist('Business Central Account not connected / token expired')

    test_func(accounting_export)

    assert accounting_export.status == 'FAILED'
    assert accounting_export.detail == {'accounting_export_id': accounting_export.id, 'message': 'Business Central Account not connected / token expired'}

    @handle_business_central_exceptions()
    def test_func(accounting_export):
        raise WrongParamsError(response = 'Error', msg = 'Error')

    test_func(accounting_export)

    error = Error.objects.filter(workspace_id=workspace_id, accounting_export=accounting_export).first()
    assert accounting_export.status == 'FAILED'
    assert accounting_export.detail == None
    assert error.type == 'BUSINESS_CENTRAL_ERROR'
    assert error.is_resolved == False

    @handle_business_central_exceptions()
    def test_func(accounting_export):
        raise InvalidTokenError(response = 'Error', msg = 'Error')

    test_func(accounting_export)

    business_central_credentials = BusinessCentralCredentials.objects.filter(workspace_id=workspace_id).first()
    assert business_central_credentials.is_expired == True
    assert business_central_credentials.refresh_token == None

    @handle_business_central_exceptions()
    def test_func(accounting_export):
        raise BulkError(response = 'Error', msg = 'Error')

    test_func(accounting_export)

    assert accounting_export.status == 'FAILED'
    assert accounting_export.detail == 'Error'

    @handle_business_central_exceptions()
    def test_func(accounting_export):
        raise Exception('Error')

    test_func(accounting_export)

    assert accounting_export.status == 'FATAL'
