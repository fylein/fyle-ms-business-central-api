"""
Fyle Serializers
"""
import logging
from datetime import datetime, timezone

from django.db.models import Q
from fyle_accounting_mappings.models import ExpenseAttribute
from fyle_integrations_platform_connector import PlatformConnector
from rest_framework import serializers
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import status

from apps.fyle.helpers import get_expense_fields
from apps.fyle.models import ExpenseFilter, Expense
from apps.workspaces.models import FyleCredential, Workspace

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


class ImportFyleAttributesSerializer(serializers.Serializer):
    """
    Import Fyle Attributes serializer
    """

    def create(self, validated_data):
        """
        Import Fyle Attributes
        """
        try:
            workspace_id = self.context['request'].parser_context.get('kwargs').get('workspace_id')
            refresh = self.context['request'].data.get('refresh')

            workspace = Workspace.objects.get(id=workspace_id)
            fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)
            platform = PlatformConnector(fyle_credentials)

            if refresh:
                platform.import_fyle_dimensions()
                workspace.source_synced_at = datetime.now()
                workspace.save(update_fields=['source_synced_at'])

            else:
                if workspace.source_synced_at:
                    time_interval = datetime.now(timezone.utc) - workspace.source_synced_at

                if workspace.source_synced_at is None or time_interval.days > 0:
                    platform.import_fyle_dimensions()
                    workspace.source_synced_at = datetime.now()
                    workspace.save(update_fields=['source_synced_at'])

            return Response(status=status.HTTP_200_OK)

        except FyleCredential.DoesNotExist:
            raise serializers.ValidationError({'message': 'Fyle credentials not found in workspace'}, code='invalid_login')

        except Exception as exception:
            logger.error('Something unexpected happened workspace_id: %s %s', workspace_id, exception)
            raise APIException("Internal Server Error", code='server_error')


class FyleFieldsSerializer(serializers.Serializer):
    """
    Fyle Fields Serializer
    """

    attribute_type = serializers.CharField()
    display_name = serializers.CharField()
    is_dependant = serializers.BooleanField()

    def format_fyle_fields(self, workspace_id):
        """
        Get Fyle Fields
        """

        attribute_types = ['EMPLOYEE', 'CATEGORY', 'PROJECT', 'COST_CENTER', 'TAX_GROUP', 'CORPORATE_CARD', 'MERCHANT']

        attributes = ExpenseAttribute.objects.filter(
            ~Q(attribute_type__in=attribute_types),
            workspace_id=workspace_id
        ).values('attribute_type', 'display_name', 'detail__is_dependent').distinct()

        attributes_list = [
            {'attribute_type': 'COST_CENTER', 'display_name': 'Cost Center', 'is_dependant': False},
            {'attribute_type': 'PROJECT', 'display_name': 'Project', 'is_dependant': False}
        ]

        for attr in attributes:
            attributes_list.append({
                'attribute_type': attr['attribute_type'],
                'display_name': attr['display_name'],
                'is_dependant': attr['detail__is_dependent']
            })

        return attributes_list


class ExpenseFieldSerializer(serializers.Serializer):
    """
    Workspace Admin Serializer
    """
    field_name = serializers.CharField()
    type = serializers.CharField()
    is_custom = serializers.BooleanField()

    def get_expense_fields(self, workspace_id:int):
        """
        Get Expense Fields
        """

        expense_fields = get_expense_fields(workspace_id=workspace_id)

        return expense_fields


class ExpenseSerializer(serializers.ModelSerializer):
    """
    Expense serializer
    """

    class Meta:
        model = Expense
        fields = ['updated_at', 'claim_number', 'employee_email', 'employee_name', 'fund_source', 'expense_number', 'payment_number', 'vendor', 'category', 'amount', 'report_id', 'settlement_id', 'expense_id']
