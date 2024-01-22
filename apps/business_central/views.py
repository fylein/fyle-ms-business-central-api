from rest_framework import generics

from apps.business_central.serializers import (
    BusinessCentralFieldSerializer,
    CompanySelectionSerializer,
    ImportBusinessCentralAttributesSerializer,
)
from apps.workspaces.models import Workspace


class ImportBusinessCentralAttributesView(generics.CreateAPIView):
    """
    Import Business Central Attributes View
    """
    serializer_class = ImportBusinessCentralAttributesSerializer


class BusinessCentralFieldsView(generics.ListAPIView):
    """
    Business Central Fields View
    """
    serializer_class = BusinessCentralFieldSerializer
    pagination_class = None

    def get_queryset(self):
        return BusinessCentralFieldSerializer().format_business_central_fields(self.kwargs["workspace_id"])


class CompanySelectionView(generics.ListCreateAPIView):
    """
    Retrieve Company Selection
    """
    serializer_class = CompanySelectionSerializer

    def get_queryset(self):
        return Workspace.objects.filter(id=self.kwargs['workspace_id'])
