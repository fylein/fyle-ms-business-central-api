import logging

from rest_framework import generics

from apps.business_central.serializers import ImportBusinessCentralAttributesSerializer, BusinessCentralFieldSerializer


logger = logging.getLogger(__name__)
logger.level = logging.INFO


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

    def get_queryset(self):
        return BusinessCentralFieldSerializer().format_business_central_fields(self.kwargs["workspace_id"])
