import logging

from django.contrib.auth import get_user_model
from fyle_rest_auth.utils import AuthUtils
from rest_framework import generics
from rest_framework.views import Response, status

from apps.workspaces.models import AdvancedSetting, BusinessCentralCredentials, ExportSetting, ImportSetting, Workspace
from apps.workspaces.serializers import (
    AdvancedSettingSerializer,
    BusinessCentralCredentialSerializer,
    ExportSettingsSerializer,
    ImportSettingsSerializer,
    WorkspaceAdminSerializer,
    WorkspaceSerializer,
)
from apps.workspaces.tasks import export_to_business_central
from ms_business_central_api.utils import assert_valid

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
    serializer_class = BusinessCentralCredentialSerializer
    lookup_field = 'workspace_id'

    queryset = BusinessCentralCredentials.objects.all()


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
    pagination_class = None

    def get_queryset(self):
        return WorkspaceAdminSerializer().get_admin_emails(self.kwargs['workspace_id'])


class TriggerExportsView(generics.GenericAPIView):
    """
    Trigger exports creation
    """

    def post(self, request, *args, **kwargs):
        export_to_business_central(workspace_id=kwargs['workspace_id'])

        return Response(
            status=status.HTTP_200_OK
        )
