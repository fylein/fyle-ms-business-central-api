import logging

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import status

from apps.fyle.helpers import get_exportable_accounting_exports_ids
from apps.fyle.models import Expense, ExpenseFilter
from apps.fyle.queue import queue_import_credit_card_expenses, queue_import_reimbursable_expenses
from apps.fyle.serializers import (
    ExpenseFieldSerializer,
    ExpenseFilterSerializer,
    ExpenseSerializer,
    FyleFieldsSerializer,
    ImportFyleAttributesSerializer,
)
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
    pagination_class = None

    def get_queryset(self):
        return FyleFieldsSerializer().format_fyle_fields(self.kwargs["workspace_id"])


class CustomFieldView(generics.ListAPIView):
    """
    Custom Field view
    """

    serializer_class = ExpenseFieldSerializer
    pagination_class = None

    def get_queryset(self):
        return ExpenseFieldSerializer().get_expense_fields(self.kwargs["workspace_id"])


class ExportableExpenseGroupsView(generics.RetrieveAPIView):
    """
    List Exportable Expense Groups
    """
    def get(self, request, *args, **kwargs):

        exportable_ids = get_exportable_accounting_exports_ids(workspace_id=kwargs['workspace_id'])

        return Response(
            data={'exportable_accounting_export_ids': exportable_ids},
            status=status.HTTP_200_OK
        )


class AccoutingExportSyncView(generics.CreateAPIView):
    """
    Create expense groups
    """
    def post(self, request, *args, **kwargs):
        """
        Post expense groups creation
        """

        queue_import_reimbursable_expenses(kwargs['workspace_id'], synchronous=True)
        queue_import_credit_card_expenses(kwargs['workspace_id'], synchronous=True)

        return Response(
            status=status.HTTP_200_OK
        )


class SkippedExpenseView(generics.ListAPIView):
    """
    List Skipped Expenses
    """
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = {'org_id': {'exact'}, 'is_skipped': {'exact'}, 'updated_at': {'gte', 'lte'}}
    ordering_fields = ('-updated_at',)
