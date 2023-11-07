"""
Fyle Serializers
"""
import logging
from rest_framework import serializers

from apps.fyle.models import ExpenseFilter

logger = logging.getLogger(__name__)
logger.level = logging.INFO


class ExpenseFilterSerializer(serializers.ModelSerializer):
    """
    Expense Filter Serializer
    """

    class Meta:
        model = ExpenseFilter
        fields = '__all__'
        read_only_fields = ('id', 'workspace', 'created_at', 'updated_at')
