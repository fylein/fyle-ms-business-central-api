import logging

from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import status

from apps.fyle.helpers import get_exportable_accounting_exports_ids
from apps.fyle.models import ExpenseFilter
from apps.fyle.serializers import (
    ExpenseFieldSerializer,
    ExpenseFilterSerializer,
    FyleFieldsSerializer,
    ImportFyleAttributesSerializer,
)
from apps.workspaces.models import Workspace
from ms_business_central_api.utils import LookupFieldMixin

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


class ExportableExpenseGroupsView(generics.RetrieveAPIView):
    """
    List Exportable Expense Groups
    """
    def get(self, request, *args, **kwargs):

        exportable_ids = get_exportable_accounting_exports_ids(workspace_id=kwargs['workspace_id'])

        return Response(
            data={'exportable_expense_group_ids': exportable_ids},
            status=status.HTTP_200_OK
        )
