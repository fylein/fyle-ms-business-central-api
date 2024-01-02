from rest_framework import generics

from apps.business_central.serializers import (
    BusinessCentralFieldSerializer,
    CompanySelectionSerializer,
    ImportBusinessCentralAttributesSerializer,
)


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


class CompanySelectionView(generics.CreateAPIView):
    """
    Retrieve Company Selection
    """
    serializer_class = CompanySelectionSerializer
