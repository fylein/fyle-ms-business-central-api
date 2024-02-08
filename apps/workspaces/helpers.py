import base64
import json
import logging

import requests
from django.conf import settings
from dynamics.exceptions.dynamics_exceptions import InternalServerError, InvalidTokenError
from future.moves.urllib.parse import urlencode

from apps.workspaces.models import BusinessCentralCredentials

logger = logging.getLogger(__name__)


def generate_token(authorization_code: str, redirect_uri: str) -> str:
    """
    Generates a token using the provided authorization code.

    :param authorization_code: Authorization code obtained from Business Central.
    :param redirect_uri: Optional redirect URI for the token request.
    :return: Response object containing the token.
    """
    api_data = {
        "grant_type": "authorization_code",
        "code": authorization_code,
        "redirect_uri": redirect_uri,
    }

    auth = "{0}:{1}".format(settings.BUSINESS_CENTRAL_CLIENT_ID, settings.BUSINESS_CENTRAL_CLIENT_SECRET)
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


def generate_business_central_refresh_token(authorization_code: str, redirect_uri: str) -> str:
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

    elif response.status_code == 400:
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
    refresh_token = generate_business_central_refresh_token(authorization_code, redirect_uri)

    # Retrieve or create BusinessCentralCredentials based on workspace_id
    business_central_credentials = BusinessCentralCredentials.get_active_business_central_credentials(workspace_id)

    if not business_central_credentials:
        # If BusinessCentralCredentials does not exist, create a new one
        business_central_credentials = BusinessCentralCredentials.objects.update_or_create(
            refresh_token=refresh_token, workspace_id=workspace_id, is_expired=False
        )
    else:
        # If BusinessCentralCredentials exists, update refresh_token and reset expiration status
        business_central_credentials.refresh_token = refresh_token
        business_central_credentials.is_expired = False
        business_central_credentials.save()

    return business_central_credentials
