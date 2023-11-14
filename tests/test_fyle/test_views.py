import json
from unittest import mock
from django.urls import reverse
from apps.workspaces.models import FyleCredential, Workspace
from tests.helpers import dict_compare_keys
from .fixtures import fixtures as data


def test_expense_filters(api_client, test_connection, create_temp_workspace, add_fyle_credentials, add_expense_filters):
    url = reverse('expense-filters', kwargs={'workspace_id': 1})

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))
    response = api_client.get(url)
    assert response.status_code == 200
    response = json.loads(response.content)

    assert dict_compare_keys(response, data['expense_filters_response']) == [], 'expense group api return diffs in keys'

    url = reverse('expense-filters', kwargs={'workspace_id': 1, 'pk': 1})

    response = api_client.delete(url, content_type='application/json')
    assert response.status_code == 204

    url = reverse('expense-filters', kwargs={'workspace_id': 1})

    response = api_client.get(url)
    assert response.status_code == 200
    assert dict_compare_keys(response, data['expense_filters_response']['results'][1]) == [], 'expense group api return diffs in keys'


def test_import_fyle_attributes(mocker, api_client, test_connection, create_temp_workspace, add_fyle_credentials):
    mocker.patch('fyle_integrations_platform_connector.fyle_integrations_platform_connector.PlatformConnector.import_fyle_dimensions', return_value=[])

    url = reverse('import-fyle-attributes', kwargs={'workspace_id': 1})

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))

    payload = {'refresh': True}

    response = api_client.post(url, payload)
    assert response.status_code == 201

    payload = {'refresh': False}

    response = api_client.post(url, payload)
    assert response.status_code == 201

    workspace = Workspace.objects.get(id=1)
    workspace.source_synced_at = None
    workspace.save()

    response = api_client.post(url, payload)
    assert response.status_code == 201

    fyle_credentials = FyleCredential.objects.get(workspace_id=1)
    fyle_credentials.delete()

    response = api_client.post(url, payload)
    assert response.status_code == 400
    assert response.data['message'] == 'Fyle credentials not found in workspace'

    with mock.patch('apps.workspaces.models.FyleCredential.objects.get') as mock_call:
        mock_call.side_effect = Exception()
        response = api_client.post(url, payload)
        assert response.status_code == 500
