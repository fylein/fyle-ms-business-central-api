import logging

from rest_framework import generics

from apps.business_central.serializers import ImportBusinessCentralAttributesSerializer


logger = logging.getLogger(__name__)
logger.level = logging.INFO


class ImportBusinessCentralAttributesView(generics.CreateAPIView):
    """
    Import Business Central Attributes View
    """
    serializer_class = ImportBusinessCentralAttributesSerializer
