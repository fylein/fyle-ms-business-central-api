import base64
import json
import logging

import requests
from django.conf import settings
from dynamics.exceptions.dynamics_exceptions import InternalServerError, InvalidTokenError
from future.moves.urllib.parse import urlencode

from apps.business_central.utils import BusinessCentralConnector
from apps.workspaces.models import BusinessCentralCredentials, Workspace

logger = logging.getLogger(__name__)


def generate_token(authorization_code: str, redirect_uri: str = None) -> str:
    """
    Generates a token using the provided authorization code.

    :param authorization_code: Authorization code obtained from Business Central.
    :param redirect_uri: Optional redirect URI for the token request.
    :return: Response object containing the token.
    """
    api_data = {
        "grant_type": "authorization_code",
        "code": authorization_code,
        "redirect_uri": settings.BUSINESS_CENTRAL_REDIRECT_URI
        if not redirect_uri
        else redirect_uri,
    }

    auth = "{0}:{1}".format(settings.BUSINESS_CENTRAL_ID, settings.BUSINESS_CENTRAL_SECRET)
    auth = base64.b64encode(auth.encode("utf-8"))

    request_header = {
        "Accept": "application/json",
        "Content-type": "application/x-www-form-urlencoded",
        "Authorization": "Basic {0}".format(str(auth.decode())),
    }

    token_url = settings.BUSINESS_CENTRAL_TOKEN_URI
    response = requests.post(
        url=token_url, data=urlencode(api_data), headers=request_header
    )
    return response


def generate_business_central_refresh_token(authorization_code: str, redirect_uri: str = None) -> str:
    """
    Generates a Business Central refresh token from the provided authorization code.

    :param authorization_code: Authorization code obtained from Business Central.
    :param redirect_uri: Optional redirect URI for the token request.
    :return: Refresh token.
    :raises InvalidTokenError: If the token request fails with a 401 status code.
    :raises InternalServerError: If the token request fails with a 500 status code.
    """
    response = generate_token(authorization_code, redirect_uri)

    if response.status_code == 200:
        successful_response = json.loads(response.text)
        return successful_response["refresh_token"]

    elif response.status_code == 401:
        raise InvalidTokenError(
            "Wrong client secret or/and refresh token", response.text
        )

    elif response.status_code == 500:
        raise InternalServerError("Internal server error", response.text)


def connect_business_central(authorization_code, redirect_uri, workspace_id):
    """
    Connects to Business Central, retrieves or generates refresh token, and updates workspace information.

    :param authorization_code: Authorization code obtained from Business Central.
    :param redirect_uri: Optional redirect URI for the token request.
    :param workspace_id: ID of the workspace.
    :return: BusinessCentralCredentials object.
    """
    if redirect_uri:
        # If redirect_uri is provided, use it in the token request
        refresh_token = generate_business_central_refresh_token(authorization_code, redirect_uri)
    else:
        # If redirect_uri is not provided, use the default redirect_uri in the token request
        refresh_token = generate_business_central_refresh_token(authorization_code)

    # Retrieve or create BusinessCentralCredentials based on workspace_id
    business_central_credentials = BusinessCentralCredentials.objects.filter(workspace_id=workspace_id).first()

    workspace = Workspace.objects.get(pk=workspace_id)

    if not business_central_credentials:
        # If BusinessCentralCredentials does not exist, create a new one
        business_central_credentials = BusinessCentralCredentials.objects.create(
            refresh_token=refresh_token, workspace_id=workspace_id
        )
    else:
        # If BusinessCentralCredentials exists, update refresh_token and reset expiration status
        business_central_credentials.refresh_token = refresh_token
        business_central_credentials.is_expired = False
        business_central_credentials.save()

    if workspace and not workspace.business_central_company_id:
        # If workspace has no associated Business Central company ID, fetch and update it
        business_central_connector = BusinessCentralConnector(business_central_credentials, workspace_id=workspace_id)
        connections = business_central_connector.connection.connections.get_all()
        connection = list(
            filter(
                lambda connection: connection["id"] == workspace.business_central_company_id,
                connections,
            )
        )

        if connection:
            # If a matching connection is found, update workspace's Business Central company ID
            workspace.business_central_company_id = connection[0]["id"]
            workspace.save()

    if workspace.onboarding_state == "COMPANY_SELECTION":
        # If workspace's onboarding state is "COMPANY_SELECTION", update it to "EXPORT_SETTINGS"
        workspace.onboarding_state = "EXPORT_SETTINGS"
        workspace.save()

    return business_central_credentials
