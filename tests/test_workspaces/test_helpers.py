from apps.workspaces.helpers import (
    generate_token,
    generate_business_central_refresh_token,
    connect_business_central
)
from dynamics.exceptions.dynamics_exceptions import (
    InternalServerError,
    InvalidTokenError
)
from apps.workspaces.models import BusinessCentralCredentials
from requests import Response


def test_generate_token(mocker):
    auth_code = "random_auth_code"
    redirect_uri = "https://redirect_uri.com"

    mock_response = Response()
    mock_response.status_code = 200
    mock_response._content = b'{"refresh_token": "token123"}'

    mocker.patch(
        "requests.post",
        return_value=mock_response
    )

    response = generate_token(auth_code, redirect_uri)
    assert response.status_code == 200
    assert response.text == '{"refresh_token": "token123"}'


def test_generate_business_central_refresh_token_success(mocker):
    auth_code = "random_auth_code"
    redirect_uri = "https://redirect_uri.com"

    mock_response = Response()
    mock_response.status_code = 200
    mock_response._content = b'{"refresh_token": "token123"}'

    mocker.patch(
        "apps.workspaces.helpers.generate_token",
        return_value=mock_response
    )

    response = generate_business_central_refresh_token(auth_code, redirect_uri)
    assert response == "token123"


def test_generate_business_central_refresh_token_failure(mocker):
    auth_code = "random_auth_code"
    redirect_uri = "https://redirect_uri.com"

    mock_response = Response()
    mock_response.status_code = 500
    mock_response._content = b'{"error": "Something is wrong"}'

    with mocker.patch(
        "apps.workspaces.helpers.generate_token",
        return_value=mock_response
    ):
        try:
            generate_business_central_refresh_token(auth_code, redirect_uri)
        except InternalServerError as e:
            assert str(e) == "'Internal server error'"

    mock_response.status_code = 400

    with mocker.patch(
        "apps.workspaces.helpers.generate_token",
        return_value=mock_response
    ):
        try:
            generate_business_central_refresh_token(auth_code, redirect_uri)
        except InvalidTokenError as e:
            assert str(e) == "'Wrong client secret or/and refresh token'"


def test_connect_business_central(
    db,
    mocker,
    create_temp_workspace,
    add_business_central_creds,
):
    auth_code = "random_auth_code"
    redirect_uri = "https://redirect_uri.com"
    workspace_id = 1

    mocker.patch(
        "apps.workspaces.helpers.generate_business_central_refresh_token",
        return_value="token123"
    )

    business_cred = connect_business_central(
        authorization_code=auth_code,
        redirect_uri=redirect_uri,
        workspace_id=workspace_id
    )
    assert business_cred.refresh_token == "token123"
    assert business_cred.is_expired == False

    business_credentials = BusinessCentralCredentials.objects.get(workspace_id=workspace_id)
    business_credentials.delete()

    business_cred = connect_business_central(
        authorization_code=auth_code,
        redirect_uri=redirect_uri,
        workspace_id=workspace_id
    )

    assert business_cred.refresh_token == "token123"
    assert business_cred.is_expired == False
