import logging
from django.contrib.auth import get_user_model

from rest_framework import generics
from rest_framework.views import Response, status

from fyle_rest_auth.utils import AuthUtils


from ms_business_central_api.utils import assert_valid
from apps.workspaces.helpers import connect_business_central
from apps.workspaces.models import (
    Workspace,
    ExportSetting,
    ImportSetting,
    AdvancedSetting,
    BusinessCentralCredentials
)
from apps.workspaces.serializers import (
    WorkspaceSerializer,
    BusinessCentralCredentialSerializer,
    ExportSettingsSerializer,
    ImportSettingsSerializer,
    AdvancedSettingSerializer,
    WorkspaceAdminSerializer
)


logger = logging.getLogger(__name__)
logger.level = logging.INFO

User = get_user_model()
auth_utils = AuthUtils()


class WorkspaceView(generics.CreateAPIView, generics.RetrieveAPIView):
    """
    Create Retrieve Workspaces
    """
    serializer_class = WorkspaceSerializer

    def get_object(self):
        """
        return workspace object for the given org_id
        """
        user_id = self.request.user

        org_id = self.request.query_params.get('org_id')

        assert_valid(org_id is not None, 'org_id is missing')

        workspace = Workspace.objects.filter(org_id=org_id, user__user_id=user_id).first()

        assert_valid(
            workspace is not None,
            'Workspace not found or the user does not have access to workspaces'
        )

        return workspace


class ReadyView(generics.RetrieveAPIView):
    """
    Ready call to check if the api is ready
    """
    authentication_classes = []
    permission_classes = []

    def get(self, request, *args, **kwargs):
        """
        Ready call
        """
        Workspace.objects.first()

        return Response(
            data={
                'message': 'Ready'
            },
            status=status.HTTP_200_OK
        )


class ConnectBusinessCentralView(generics.CreateAPIView, generics.RetrieveAPIView):
    """
    Business Central Connect Oauth View
    """

    def post(self, request, **kwargs):
        """
        Post of Business Central Credentials
        """

        authorization_code = request.data.get("code")
        redirect_uri = request.data.get("redirect_uri")

        business_central_credentials = connect_business_central(
            authorization_code=authorization_code,
            redirect_uri=redirect_uri,
            workspace_id=kwargs["workspace_id"],
        )

        return Response(
            data=BusinessCentralCredentialSerializer(business_central_credentials).data,
            status=status.HTTP_200_OK,
        )

    def get(self, request, **kwargs):
        """
        Get Business Central Credentials in Workspace
        """

        business_central_credentials = BusinessCentralCredentials.objects.get(
            workspace_id=kwargs["workspace_id"],
            is_expired=False,
            refresh_token__isnull=False,
        )

        return Response(
            data=BusinessCentralCredentialSerializer(business_central_credentials).data,
            status=status.HTTP_200_OK,
        )


class ExportSettingView(generics.CreateAPIView, generics.RetrieveAPIView):
    """
    Retrieve or Create Export Settings
    """
    serializer_class = ExportSettingsSerializer
    lookup_field = 'workspace_id'

    queryset = ExportSetting.objects.all()


class ImportSettingView(generics.CreateAPIView, generics.RetrieveAPIView):
    """
    Retrieve or Create Import Settings
    """
    serializer_class = ImportSettingsSerializer
    lookup_field = 'workspace_id'

    queryset = ImportSetting.objects.all()


class AdvancedSettingView(generics.CreateAPIView, generics.RetrieveAPIView):
    """
    Retrieve or Create Advanced Settings
    """
    serializer_class = AdvancedSettingSerializer
    lookup_field = 'workspace_id'
    lookup_url_kwarg = 'workspace_id'

    queryset = AdvancedSetting.objects.all()


class WorkspaceAdminsView(generics.ListAPIView):
    """
    Retrieve Workspace Admins
    """
    serializer_class = WorkspaceAdminSerializer
    queryset = Workspace.objects.all()
