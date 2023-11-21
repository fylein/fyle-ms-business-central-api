import pytest
from django.urls import reverse

from tests.test_fyle.fixtures import fixtures as fyle_data


@pytest.mark.django_db(databases=['default'])
def test_setup():
    assert 1 == 1


def test_get_all_orgs_view(api_client, test_connection, create_temp_workspace, add_fyle_credentials, mocker):

    access_token = test_connection.access_token
    url = reverse('fyle-orgs')

    mocker.patch(
        'apps.users.views.get_fyle_orgs',
        return_value=fyle_data['get_all_orgs']
    )

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(access_token))

    response = api_client.get(url)
    assert response.status_code == 200
    assert response.data == fyle_data['get_all_orgs']
