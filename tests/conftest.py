"""
Fixture configuration for all the tests
"""
from datetime import datetime, timezone
from unittest import mock

import pytest
from fyle.platform.platform import Platform
from fyle_accounting_mappings.models import DestinationAttribute, MappingSetting
from fyle_rest_auth.models import AuthToken, User
from rest_framework.test import APIClient

from apps.accounting_exports.models import AccountingExport, AccountingExportSummary, Error
from apps.fyle.helpers import get_access_token
from apps.fyle.models import ExpenseFilter
from apps.workspaces.models import BusinessCentralCredentials, ExportSetting, FyleCredential, ImportSetting, Workspace
from ms_business_central_api.tests import settings
from tests.test_fyle.fixtures import fixtures as fyle_fixtures


@pytest.fixture()
def api_client():
    """
    Fixture required to test views
    """
    return APIClient()


@pytest.fixture()
def test_connection(db):
    """
    Creates a connection with Fyle
    """
    client_id = settings.FYLE_CLIENT_ID
    client_secret = settings.FYLE_CLIENT_SECRET
    token_url = settings.FYLE_TOKEN_URI
    refresh_token = 'Dummy.Refresh.Token'
    server_url = settings.FYLE_BASE_URL

    fyle_connection = Platform(
        token_url=token_url,
        client_id=client_id,
        client_secret=client_secret,
        refresh_token=refresh_token,
        server_url=server_url
    )

    access_token = get_access_token(refresh_token)
    fyle_connection.access_token = access_token
    user_profile = fyle_connection.v1.spender.my_profile.get()['data']
    user = User(
        password='', last_login=datetime.now(tz=timezone.utc), id=1, email=user_profile['user']['email'],
        user_id=user_profile['user_id'], full_name='', active='t', staff='f', admin='t'
    )

    user.save()

    auth_token = AuthToken(
        id=1,
        refresh_token=refresh_token,
        user=user
    )
    auth_token.save()

    return fyle_connection


@pytest.fixture(scope="session", autouse=True)
def default_session_fixture(request):
    patched_1 = mock.patch(
        'dynamics.core.client.Dynamics._Dynamics__refresh_access_token',
        return_value="dummy_token"
    )
    patched_1.__enter__()

    patched_2 = mock.patch(
        'fyle_rest_auth.authentication.get_fyle_admin',
        return_value=fyle_fixtures['get_my_profile']
    )
    patched_2.__enter__()

    patched_3 = mock.patch(
        'fyle.platform.internals.auth.Auth.update_access_token',
        return_value='asnfalsnkflanskflansfklsan'
    )
    patched_3.__enter__()

    patched_4 = mock.patch(
        'apps.fyle.helpers.post_request',
        return_value={
            'access_token': 'easnfkjo12233.asnfaosnfa.absfjoabsfjk',
            'cluster_domain': 'https://staging.fyle.tech'
        }
    )
    patched_4.__enter__()

    patched_5 = mock.patch(
        'fyle.platform.apis.v1.spender.MyProfile.get',
        return_value=fyle_fixtures['get_my_profile']
    )
    patched_5.__enter__()

    patched_6 = mock.patch(
        'fyle_rest_auth.helpers.get_fyle_admin',
        return_value=fyle_fixtures['get_my_profile']
    )
    patched_6.__enter__()


@pytest.fixture
@pytest.mark.django_db(databases=['default'])
def create_temp_workspace():
    """
    Pytest fixture to create a temorary workspace
    """
    workspace_ids = [
        1, 2, 3
    ]
    for workspace_id in workspace_ids:
        Workspace.objects.create(
            id=workspace_id,
            name='Fyle For Testing {}'.format(workspace_id),
            org_id='riseabovehate{}'.format(workspace_id),
            reimbursable_last_synced_at=None,
            credit_card_last_synced_at=None,
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc)
        )


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def add_fyle_credentials():
    """
    Pytest fixture to add fyle credentials to a workspace
    """
    workspace_ids = [
        1, 2, 3
    ]
    for workspace_id in workspace_ids:
        FyleCredential.objects.create(
            refresh_token='dummy_refresh_token',
            workspace_id=workspace_id,
            cluster_domain='https://dummy_cluster_domain.com',
        )


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def add_accounting_export_expenses():
    """
    Pytest fixture to add accounting export to a workspace
    """
    workspace_ids = [
        1, 2, 3
    ]
    for workspace_id in workspace_ids:
        AccountingExport.objects.update_or_create(
            workspace_id=workspace_id,
            type='FETCHING_REIMBURSABLE_EXPENSES',
            defaults={
                'status': 'IN_PROGRESS'
            }
        )

        AccountingExport.objects.update_or_create(
            workspace_id=workspace_id,
            type='FETCHING_CREDIT_CARD_EXPENENSES',
            defaults={
                'status': 'IN_PROGRESS'
            }
        )


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def add_accounting_export_summary():
    """
    Pytest fixture to add accounting export summary to a workspace
    """
    workspace_ids = [
        1, 2, 3
    ]
    for workspace_id in workspace_ids:
        AccountingExportSummary.objects.create(
            workspace_id=workspace_id,
            last_exported_at = datetime.now(tz=timezone.utc),
            next_export_at = datetime.now(tz=timezone.utc),
            export_mode = 'AUTO',
            total_accounting_export_count = 10,
            successful_accounting_export_count = 5,
            failed_accounting_export_count = 5
        )


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def add_errors():
    """
    Pytest fixture to add errors to a workspace
    """
    workspace_ids = [
        1, 2, 3
    ]
    for workspace_id in workspace_ids:
        Error.objects.create(
            type='EMPLOYEE_MAPPING',
            is_resolved=False,
            error_title='Employee Mapping Error',
            error_detail='Employee Mapping Error',
            workspace_id=workspace_id
        )
        Error.objects.create(
            type='CATEGORY_MAPPING',
            is_resolved=False,
            error_title='Category Mapping Error',
            error_detail='Category Mapping Error',
            workspace_id=workspace_id
        )
        Error.objects.create(
            type='BUSINESS_CENTRAL_ERROR',
            is_resolved=False,
            error_title='Business Central Error',
            error_detail='Business Central Error',
            workspace_id=workspace_id
        )


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def add_expense_filters():
    """
    Pytest fixture to add expense filters to a workspace
    """
    workspace_ids = [
        1, 2, 3
    ]
    for workspace_id in workspace_ids:
        ExpenseFilter.objects.create(
            condition='employee_email',
            operator='in',
            values=['ashwinnnnn.t@fyle.in', 'admin1@fyleforleaf.in'],
            rank="1",
            join_by='AND',
            is_custom=False,
            custom_field_type='SELECT',
            workspace_id=workspace_id
        )
        ExpenseFilter.objects.create(
            condition='last_spent_at',
            operator='lt',
            values=['2020-04-20 23:59:59+00'],
            rank="2",
            join_by=None,
            is_custom=False,
            custom_field_type='SELECT',
            workspace_id=workspace_id
        )


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def add_business_central_creds():
    """
    Pytest fixture to add business central credentials to a workspace
    """
    workspace_ids = [
        1, 2, 3
    ]
    for workspace_id in workspace_ids:
        BusinessCentralCredentials.objects.create(
            refresh_token = 'dummy_refresh_token',
            is_expired = False,
            workspace_id = workspace_id
        )


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def add_destination_attributes():
    """
    Pytest fixture to add destination attributes to a workspace
    """
    workspace_ids = [
        1, 2, 3
    ]
    for workspace_id in workspace_ids:
        DestinationAttribute.objects.create(
            attribute_type='DUMMY_ATTRIBUTE_TYPE',
            display_name='dummy_attribute_name',
            value='dummy_attribute_value',
            destination_id='dummy_destination_id',
            active=True,
            workspace_id=workspace_id
        )


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def add_export_settings():
    """
    Pytest fixtue to add export_settings to a workspace
    """

    workspace_ids = [
        1, 2, 3
    ]

    for workspace_id in workspace_ids:
        ExportSetting.objects.create(
            workspace_id=workspace_id,
            reimbursable_expenses_export_type='BILL' if workspace_id in [1, 2] else 'JOURNAL_ENTRY',
            default_bank_account_name='Accounts Payable',
            default_bank_account_id='1',
            reimbursable_expense_state='PAYMENT_PROCESSING',
            reimbursable_expense_date='spent_at' if workspace_id == 1 else 'last_spent_at',
            reimbursable_expense_grouped_by='REPORT' if workspace_id == 1 else 'EXPENSE',
            credit_card_expense_export_type='CREDIT_CARD_PURCHASE' if workspace_id in [1, 2] else 'JOURNAL_ENTRY',
            credit_card_expense_state='PAYMENT_PROCESSING',
            credit_card_expense_grouped_by='EXPENSE' if workspace_id == 3 else 'REPORT',
            credit_card_expense_date='spent_at'
        )


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def add_import_settings():
    """
    Pytest fixtue to add import_settings to a workspace
    """
    workspace_ids = [
        1, 2, 3
    ]

    for workspace_id in workspace_ids:
        ImportSetting.objects.create(
            workspace_id=workspace_id,
            import_vendors_as_merchants=True,
            import_categories=True
        )


@pytest.fixture()
@pytest.mark.django_db(databases=['default'])
def add_mapping_settings():
    """
    Pytest fixtue to add mapping_settings to a workspace
    """
    workspace_ids = [
        1, 2, 3
    ]

    for workspace_id in workspace_ids:
        MappingSetting.objects.create(
            workspace_id=workspace_id,
            source_field='CATEGORY',
            destination_field='ACCOUNT',
            import_to_fyle=True,
            is_custom=False
        )
