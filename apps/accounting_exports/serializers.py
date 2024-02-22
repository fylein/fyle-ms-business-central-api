from fyle_accounting_mappings.serializers import ExpenseAttributeSerializer
from rest_framework import serializers

from apps.accounting_exports.models import AccountingExport, AccountingExportSummary, Error
from apps.fyle.serializers import ExpenseSerializer


class AccountingExportSerializer(serializers.ModelSerializer):
    """
    Accounting Export serializer
    """

    expenses = ExpenseSerializer(many=True)

    class Meta:
        model = AccountingExport
        fields = '__all__'


class AccountingExportSummarySerializer(serializers.ModelSerializer):
    """
    Accounting Export Summary serializer
    """

    class Meta:
        model = AccountingExportSummary
        fields = '__all__'


class ErrorSerializer(serializers.ModelSerializer):
    """
    Serializer for the Errors
    """

    expense_attribute = ExpenseAttributeSerializer()
    accounting_export = AccountingExportSerializer()

    class Meta:
        model = Error
        fields = '__all__'
