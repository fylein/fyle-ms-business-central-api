import json
from django.urls import reverse
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
