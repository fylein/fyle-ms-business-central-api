import json
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


def test_sage300_fields(api_client, test_connection):
    workspace_id = 1

    access_token = test_connection.access_token
    url = reverse('business-central-fields', kwargs={'workspace_id': workspace_id})

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(access_token))

    response = api_client.get(url)
    assert response.status_code == 200

    assert response.data['results'] == []