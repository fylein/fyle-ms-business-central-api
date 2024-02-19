import json
import pytest

from django.urls import reverse

from apps.workspaces.models import BusinessCentralCredentials


def test_sync_dimensions(api_client, test_connection, mocker, create_temp_workspace, add_business_central_creds):
    workspace_id = 1

    access_token = test_connection.access_token
    url = reverse('import-business-central-attributes', kwargs={'workspace_id': workspace_id})

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(access_token))

    mocker.patch('apps.business_central.helpers.sync_dimensions', return_value=None)

    response = api_client.post(url)
    assert response.status_code == 201

    business_central_credentials = BusinessCentralCredentials.objects.get(workspace_id=workspace_id)
    business_central_credentials.delete()

    response = api_client.post(url)
    assert response.status_code == 400

    response = json.loads(response.content)
    assert response['message'] == 'Business Central credentials not found / invalid in workspace'


def test_sync_dimensions_1(api_client, test_connection, mocker, create_temp_workspace, add_business_central_creds):
    workspace_id = 1

    access_token = test_connection.access_token
    url = reverse('import-business-central-attributes', kwargs={'workspace_id': workspace_id})

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(access_token))

    mocker.patch('apps.business_central.helpers.sync_dimensions', return_value=None)

    mocker.patch('apps.workspaces.models.BusinessCentralCredentials.objects.get', side_effect=Exception("Unexpected error"))

    with pytest.raises(Exception):
        response = api_client.post(url)

        assert response.status_code == 500
        assert response.data['message'] == 'Something unexpected happened'


def test_business_central_fields(api_client, test_connection, create_temp_workspace, add_fyle_credentials, add_destination_attributes):
    workspace_id = 1

    access_token = test_connection.access_token
    url = reverse('business-central-fields', kwargs={'workspace_id': workspace_id})

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(access_token))

    response = api_client.get(url)
    assert response.status_code == 200

    assert response.data == [{'attribute_type': 'DUMMY_ATTRIBUTE_TYPE', 'display_name': 'dummy_attribute_name'}]


def test_post_company_selection(api_client, test_connection):
    '''
    Test get workspace admins
    '''
    url = reverse('workspaces')
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))
    response = api_client.post(url)

    workspace_id = response.data['id']

    url = reverse('company-selection', kwargs={'workspace_id': workspace_id})
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))

    payload = {
        'company_id': '123',
        'company_name': 'Fyle Technologies'
    }

    response = api_client.post(url, payload)
    assert response.status_code == 201


def test_connection_view_1(api_client, test_connection, create_temp_workspace):
    workspace_id = 1
    url = reverse('connection', kwargs={'workspace_id': workspace_id})
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))
    response = api_client.get(url)

    assert response.status_code == 400
    assert response.data['message'] == 'Business Central credentials not found in workspace'


def test_connection_view_2(api_client, test_connection, create_temp_workspace, add_business_central_creds, mocker):
    workspace_id = 1
    url = reverse('connection', kwargs={'workspace_id': workspace_id})
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))

    business_central_credentials = BusinessCentralCredentials.objects.get(workspace_id=workspace_id)

    assert business_central_credentials.workspace.id == workspace_id
    assert business_central_credentials.refresh_token == 'dummy_refresh_token'
    assert business_central_credentials.is_expired == False

    response = api_client.get(url)

    assert response.status_code == 400
    assert response.data['message'] == 'Invalid token or Business Central connection expired'


def test_connection_view_3(
        api_client,
        test_connection,
        create_temp_workspace,
        add_business_central_creds,
        mocker
):
    workspace_id = 1
    url = reverse('connection', kwargs={'workspace_id': workspace_id})
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))

    mocker.patch(
        'apps.business_central.utils.BusinessCentralConnector.get_companies',
        return_value=[{'id': '123', 'name': 'Fyle Technologies'}]
    )

    response = api_client.get(url)

    assert response.status_code == 200
    assert response.data == [{'id': '123', 'name': 'Fyle Technologies'}]
