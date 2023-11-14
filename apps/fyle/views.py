import logging
from rest_framework import generics
from ms_business_central_api.utils import LookupFieldMixin
from apps.workspaces.models import Workspace
from apps.fyle.serializers import ExpenseFilterSerializer, ImportFyleAttributesSerializer, FyleFieldsSerializer, ExpenseFieldSerializer
from apps.fyle.models import ExpenseFilter

logger = logging.getLogger(__name__)
logger.level = logging.INFO


class ExpenseFilterView(LookupFieldMixin, generics.ListCreateAPIView):
    """
    Expense Filter view
    """

    queryset = ExpenseFilter.objects.all()
    serializer_class = ExpenseFilterSerializer


class ExpenseFilterDeleteView(generics.DestroyAPIView):
    """
    Expense Filter Delete view
    """

    queryset = ExpenseFilter.objects.all()
    serializer_class = ExpenseFilterSerializer


class ImportFyleAttributesView(generics.CreateAPIView):
    """
    Import Fyle Attributes View
    """
    serializer_class = ImportFyleAttributesSerializer


class FyleFieldsView(generics.ListAPIView):
    """
    Fyle Fields view
    """

    serializer_class = FyleFieldsSerializer

    def get_queryset(self):
        return FyleFieldsSerializer().format_fyle_fields(self.kwargs["workspace_id"])


class CustomFieldView(generics.ListAPIView):
    """
    Custom Field view
    """

    serializer_class = ExpenseFieldSerializer
    queryset = Workspace.objects.all()
