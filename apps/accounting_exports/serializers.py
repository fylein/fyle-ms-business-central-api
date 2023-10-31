from rest_framework import serializers

from apps.accounting_exports.models import AccountingExport, AccountingExportSummary


class AccountingExportSerializer(serializers.ModelSerializer):
    """
    Accounting Export serializer
    """

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
