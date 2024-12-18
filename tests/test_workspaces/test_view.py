import json

import pytest  # noqa
from django.urls import reverse
from django_q.models import Schedule
from fyle_accounting_mappings.models import MappingSetting

from apps.workspaces.models import AdvancedSetting, BusinessCentralCredentials, ExportSetting, ImportSetting, Workspace
from tests.helpers import dict_compare_keys
from tests.test_fyle.fixtures import fixtures as data


def test_post_of_workspace(api_client, test_connection):
    '''
    Test post of workspace
    '''
    url = reverse('workspaces')
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))
    response = api_client.post(url)

    workspace = Workspace.objects.filter(org_id='orNoatdUnm1w').first()

    assert response.status_code == 201
    assert workspace.name == response.data['name']
    assert workspace.org_id == response.data['org_id']
    assert workspace.onboarding_state == response.data['onboarding_state']

    response = json.loads(response.content)

    response = api_client.post(url)
    assert response.status_code == 201


def test_get_of_workspace(api_client, test_connection):
    '''
    Test get of workspace
    '''
    url = reverse('workspaces')
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))
    response = api_client.get(url)

    assert response.status_code == 400
    assert response.data['message'] == 'org_id is missing'

    response = api_client.get('{}?org_id=orNoatdUnm1w'.format(url))

    assert response.status_code == 400
    assert response.data['message'] == 'Workspace not found or the user does not have access to workspaces'

    response = api_client.post(url)
    response = api_client.get('{}?org_id=orNoatdUnm1w'.format(url))

    assert response.status_code == 200
    assert response.data['name'] == 'Fyle For MS Dynamics Demo'
    assert response.data['org_id'] == 'orNoatdUnm1w'


def test_get_of_business_central_creds(api_client, test_connection):
    '''
    Test get of Business Central Credentials
    '''
    url = reverse('workspaces')
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))
    response = api_client.post(url)

    url = reverse('business-central-credentials', kwargs={'workspace_id': response.data['id']})

    BusinessCentralCredentials.objects.create(
        refresh_token='dummy_refresh_token',
        workspace_id=response.data['id'],
        is_expired=False
    )

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))
    response = api_client.get(url)

    assert response.status_code == 200
    assert response.data['refresh_token'] == 'dummy_refresh_token'
    assert response.data['is_expired'] == False


def test_export_settings(api_client, test_connection, create_temp_workspace, add_fyle_credentials, add_business_central_creds, mocker):
    '''
    Test export settings
    '''
    url = reverse('export-settings', kwargs={'workspace_id': 1})

    mocker.patch(
        "dynamics.apis.Journals.post",
        return_value={
            "id": '1234'
        },
    )
    mocker.patch(
        "dynamics.apis.Journals.get_all",
        return_value=[],
    )

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))
    response = api_client.post(url)
    assert response.status_code == 400

    payload = {
        'reimbursable_expenses_export_type': 'PURCHASE_INVOICE',
        'reimbursable_expense_state': 'PAYMENT_PROCESSING',
        'reimbursable_expense_date': 'LAST_SPENT_AT',
        'reimbursable_expense_grouped_by': 'EXPENSE',
        'credit_card_expense_export_type': 'JOURNAL_ENTRY',
        'credit_card_expense_state': 'PAID',
        'credit_card_expense_grouped_by': 'EXPENSE',
        'credit_card_expense_date': 'CURRENT_DATE',
        "auto_create_vendors": "true",
        'default_vendor_name': 'Nilesh',
        'default_vendor_id': '123',
        'default_bank_account_id': '123',
        'default_bank_account_name': 'Bank account',
        'employee_field_mapping': 'VENDOR'
    }

    response = api_client.post(url, payload)

    export_settings = ExportSetting.objects.filter(workspace_id=1).first()

    assert response.status_code == 201
    assert export_settings.reimbursable_expenses_export_type == 'PURCHASE_INVOICE'
    assert export_settings.reimbursable_expense_state == 'PAYMENT_PROCESSING'
    assert export_settings.reimbursable_expense_date == 'LAST_SPENT_AT'
    assert export_settings.reimbursable_expense_grouped_by == 'EXPENSE'
    assert export_settings.credit_card_expense_export_type == 'JOURNAL_ENTRY'
    assert export_settings.credit_card_expense_state == 'PAID'
    assert export_settings.credit_card_expense_grouped_by == 'EXPENSE'
    assert export_settings.credit_card_expense_date == 'CURRENT_DATE'
    assert export_settings.default_vendor_name == 'Nilesh'
    assert export_settings.default_vendor_id == '123'
    assert export_settings.employee_field_mapping == 'VENDOR'

    response = api_client.get(url)

    assert response.status_code == 200
    assert export_settings.reimbursable_expenses_export_type == 'PURCHASE_INVOICE'
    assert export_settings.reimbursable_expense_state == 'PAYMENT_PROCESSING'
    assert export_settings.reimbursable_expense_date == 'LAST_SPENT_AT'
    assert export_settings.reimbursable_expense_grouped_by == 'EXPENSE'
    assert export_settings.credit_card_expense_export_type == 'JOURNAL_ENTRY'
    assert export_settings.credit_card_expense_state == 'PAID'
    assert export_settings.credit_card_expense_grouped_by == 'EXPENSE'
    assert export_settings.credit_card_expense_date == 'CURRENT_DATE'
    assert export_settings.default_vendor_name == 'Nilesh'
    assert export_settings.default_vendor_id == '123'
    assert export_settings.employee_field_mapping == 'VENDOR'


def test_import_settings(mocker, api_client, test_connection, create_temp_workspace, add_fyle_credentials):
    mocker.patch(
        'fyle_integrations_platform_connector.apis.ExpenseCustomFields.get_by_id',
        return_value={
            'options': ['samp'],
            'updated_at': '2020-06-11T13:14:55.201598+00:00',
            'is_mandatory': False
        }
    )
    mocker.patch(
        'fyle_integrations_platform_connector.apis.ExpenseCustomFields.post',
        return_value = {
            "data": {"id": 12}
        }
    )
    mocker.patch(
        'fyle_integrations_platform_connector.apis.ExpenseCustomFields.sync',
        return_value=None
    )

    mocker.patch(
        'fyle_integrations_platform_connector.apis.DependentFields.get_project_field_id',
        return_value=12
    )

    workspace = Workspace.objects.get(id=1)
    workspace.onboarding_state = 'IMPORT_SETTINGS'
    workspace.save()

    ImportSetting.objects.create(
        workspace_id=workspace.id,
        import_categories=True,
        import_vendors_as_merchants=True,
        charts_of_accounts=['Expense']
    )

    url = reverse('import-settings', kwargs={'workspace_id': 1})
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))
    response = api_client.put(
        url,
        data=data['import_settings_payload'],
        format='json'
    )

    assert response.status_code == 200

    response = json.loads(response.content)
    assert dict_compare_keys(response, data['import_settings_response']) == [], 'workspaces api returns a diff in the keys'

    response = api_client.put(
        url,
        data=data['import_settings_without_mapping'],
        format='json'
    )
    assert response.status_code == 200

    # Test if import_projects add schedule or not
    url = reverse('import-settings', kwargs={'workspace_id': 1})
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))
    response = api_client.put(
        url,
        data=data['import_settings_schedule_check'],
        format='json'
    )

    assert response.status_code == 200

    mapping = MappingSetting.objects.filter(workspace_id=1, source_field='PROJECT').first()

    assert mapping.import_to_fyle == True

    schedule = Schedule.objects.filter(
        func='apps.mappings.imports.queues.chain_import_fields_to_fyle',
        args='{}'.format(1),
    ).first()

    assert schedule.func == 'apps.mappings.imports.queues.chain_import_fields_to_fyle'
    assert schedule.args == '1'

    invalid_configurations = data['import_settings_payload']
    invalid_configurations['import_settings'] = {}
    response = api_client.put(
        url,
        data=invalid_configurations,
        format='json'
    )
    assert response.status_code == 400

    response = json.loads(response.content)
    assert response['non_field_errors'] == ['Import Settings are required']

    response = api_client.put(
        url,
        data=data['invalid_mapping_settings'],
        format='json'
    )
    assert response.status_code == 400


def test_advanced_settings(api_client, test_connection):
    '''
    Test advanced settings
    '''
    url = reverse('workspaces')
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))
    response = api_client.post(url)

    workspace_id = response.data['id']

    url = reverse('advanced-settings', kwargs={'workspace_id': workspace_id})

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))

    payload = {
        'expense_memo_structure': [
            'employee_email',
            'merchant',
            'purpose',
            'report_number',
            'expense_link'
        ],
        'schedule_is_enabled': False,
        'interval_hours': 12,
        'emails_selected': json.dumps([
            {
                'name': 'Shwetabh Kumar',
                'email': 'shwetabh.kumar@fylehq.com'
            },
            {
                'name': 'Netra Ballabh',
                'email': 'nilesh.p@fylehq.com'
            },
        ]),
        'auto_create_vendor': True
    }

    response = api_client.post(url, payload)

    assert response.status_code == 201
    assert response.data['expense_memo_structure'] == [
        'employee_email',
        'merchant',
        'purpose',
        'report_number',
        'expense_link'
    ]
    assert response.data['schedule_is_enabled'] is False
    assert response.data['emails_selected'] == [
        {
            'name': 'Shwetabh Kumar',
            'email': 'shwetabh.kumar@fylehq.com'
        },
        {
            'name': 'Netra Ballabh',
            'email': 'nilesh.p@fylehq.com'
        },
    ]
    assert response.data['auto_create_vendor'] == True

    response = api_client.get(url)

    assert response.status_code == 200
    assert response.data['expense_memo_structure'] == [
        'employee_email',
        'merchant',
        'purpose',
        'report_number',
        'expense_link'
    ]
    assert response.data['schedule_is_enabled'] is False
    assert response.data['emails_selected'] == [
        {
            'name': 'Shwetabh Kumar',
            'email': 'shwetabh.kumar@fylehq.com'
        },
        {
            'name': 'Netra Ballabh',
            'email': 'nilesh.p@fylehq.com'
        },
    ]

    del payload['expense_memo_structure']

    AdvancedSetting.objects.filter(workspace_id=workspace_id).first().delete()

    response = api_client.post(url, payload)

    assert response.status_code == 201
    assert response.data['expense_memo_structure'] == [
        'employee_email',
        'merchant',
        'purpose',
        'report_number'
    ]
    assert response.data['schedule_is_enabled'] is False
    assert response.data['emails_selected'] == [
        {
            'name': 'Shwetabh Kumar',
            'email': 'shwetabh.kumar@fylehq.com'
        },
        {
            'name': 'Netra Ballabh',
            'email': 'nilesh.p@fylehq.com'
        },
    ]


def test_get_workspace_admins(api_client, test_connection):
    '''
    Test get workspace admins
    '''
    url = reverse('workspaces')
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))
    response = api_client.post(url)

    workspace_id = response.data['id']

    url = reverse('admin', kwargs={'workspace_id': workspace_id})
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))

    response = api_client.get(url)
    assert response.status_code == 200
