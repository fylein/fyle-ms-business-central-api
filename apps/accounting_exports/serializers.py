from rest_framework import serializers

from apps.accounting_exports.models import AccountingExport


class AccountingExportSerializer(serializers.ModelSerializer):
    """
    Accounting Export serializer
    """

    class Meta:
        model = AccountingExport
        fields = '__all__'
