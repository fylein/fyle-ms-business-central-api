import logging
import base64
import requests
import json

from django.conf import settings
from future.moves.urllib.parse import urlencode
from dynamics.exceptions.dynamics_exceptions import InternalServerError, InvalidTokenError

from apps.workspaces.models import BusinessCentralCredentials, Workspace
from apps.business_central.utils import BusinessCentralConnector


logger = logging.getLogger(__name__)


def generate_token(authorization_code: str, redirect_uri: str = None) -> str:
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
    Generate Business Central refresh token from authorization code
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
    if redirect_uri:
        refresh_token = generate_business_central_refresh_token(authorization_code, redirect_uri)
    else:
        refresh_token = generate_business_central_refresh_token(authorization_code)
    business_central_credentials = BusinessCentralCredentials.objects.filter(workspace_id=workspace_id).first()

    workspace = Workspace.objects.get(pk=workspace_id)

    if not business_central_credentials:
        business_central_credentials = BusinessCentralCredentials.objects.create(
            refresh_token=refresh_token, workspace_id=workspace_id
        )
    else:
        business_central_credentials.refresh_token = refresh_token
        business_central_credentials.is_expired = False
        business_central_credentials.save()

    if workspace and not workspace.business_central_company_id:
        business_central_connector = BusinessCentralConnector(business_central_credentials, workspace_id=workspace_id)
        connections = business_central_connector.connection.connections.get_all()
        connection = list(
            filter(
                lambda connection: connection["id"] == workspace.business_central_company_id,
                connections,
            )
        )

        if connection:
            workspace.business_central_company_id = connection[0]["id"]
            workspace.save()

    if workspace.onboarding_state == "CONNECTION":
        workspace.onboarding_state = "EXPORT_SETTINGS"
        workspace.save()

    return business_central_credentials
