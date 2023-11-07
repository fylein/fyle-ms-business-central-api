import logging
from rest_framework import generics
from ms_business_central_api.utils import LookupFieldMixin
from apps.fyle.serializers import ExpenseFilterSerializer
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
