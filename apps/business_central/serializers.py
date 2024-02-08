import logging
from datetime import datetime

from django.db.models import Q
from dynamics.exceptions.dynamics_exceptions import InvalidTokenError, WrongParamsError
from fyle_accounting_mappings.models import DestinationAttribute
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import status

from apps.business_central.helpers import check_interval_and_sync_dimension, sync_dimensions
from apps.business_central.utils import BusinessCentralConnector
from apps.workspaces.models import BusinessCentralCredentials, Workspace

logger = logging.getLogger(__name__)
logger.level = logging.INFO


class ImportBusinessCentralAttributesSerializer(serializers.Serializer):
    """
    Import Business Central Attributes serializer
    """

    def create(self, validated_data):
        try:
            # Get the workspace ID from the URL kwargs
            workspace_id = self.context['request'].parser_context['kwargs']['workspace_id']

            # Check if the 'refresh' field is provided in the request data
            refresh_dimension = self.context['request'].data.get('refresh', False)

            # Retrieve the workspace and Business Central credentials
            workspace = Workspace.objects.get(pk=workspace_id)
            business_central_credentials = BusinessCentralCredentials.objects.get(workspace_id=workspace.id)

            if refresh_dimension:
                # If 'refresh' is true, perform a full sync of dimensions
                sync_dimensions(business_central_credentials, workspace.id)
            else:
                # If 'refresh' is false, check the interval and sync dimension accordingly
                check_interval_and_sync_dimension(workspace, business_central_credentials)

            # Update the destination_synced_at field and save the workspace
            workspace.destination_synced_at = datetime.now()
            workspace.save(update_fields=['destination_synced_at'])

            # Return a success response
            return Response(status=status.HTTP_200_OK)

        except BusinessCentralCredentials.DoesNotExist:
            # Handle the case when business central credentials are not found or invalid
            raise serializers.ValidationError(
                {'message': 'Business Central credentials not found / invalid in workspace'}
            )

        except Exception as exception:
            # Handle unexpected exceptions and log the error
            logger.error(
                'Something unexpected happened workspace_id: %s %s',
                workspace_id,
                exception,
            )
            # Raise a custom exception or re-raise the original exception
            raise


class BusinessCentralFieldSerializer(serializers.Serializer):
    """
    Business Central Fields Serializer
    """

    attribute_type = serializers.CharField()
    display_name = serializers.CharField()

    def format_business_central_fields(self, workspace_id):
        attribute_types = [
            "VENDOR",
            "ACCOUNT",
            "EMPLOYEE",
            "LOCATION",
            "COMPANY"
        ]
        attributes = (
            DestinationAttribute.objects.filter(
                ~Q(attribute_type__in=attribute_types),
                workspace_id=workspace_id,
            )
            .values("attribute_type", "display_name")
            .distinct()
        )

        serialized_attributes = BusinessCentralFieldSerializer(attributes, many=True).data

        attributes_list = list(serialized_attributes)

        return attributes_list


class CompanySelectionSerializer(serializers.ModelSerializer):
    """
    Company Selection Serializer
    """

    class Meta:
        model = Workspace
        fields = '__all__'
        read_only_fields = ('id', 'name', 'org_id', 'created_at', 'updated_at', 'user')

    def create(self, validated_data):
        """
        Create Company Selection
        """
        workspace_id = self.context['request'].parser_context.get('kwargs').get('workspace_id')
        workspace = Workspace.objects.get(id=workspace_id)

        workspace.business_central_company_id = self.context['request'].data.get('company_id')
        workspace.business_central_company_name = self.context['request'].data.get('company_name')
        if workspace.onboarding_state == 'COMPANY_SELECTION':
            workspace.onboarding_state = 'EXPORT_SETTINGS'
        workspace.save()

        return workspace


class Connectionserializer(serializers.Serializer):
    """
    Connection Serializer
    """

    def get_company(self, workspace_id):
        """
        Get Company
        """
        try:
            business_central_credentials: BusinessCentralCredentials = BusinessCentralCredentials.get_active_business_central_credentials(workspace_id)

            business_central_connector = BusinessCentralConnector(business_central_credentials, workspace_id=workspace_id)

            companies = business_central_connector.sync_companies()

            return Response(data=companies, status=status.HTTP_200_OK)
        except BusinessCentralCredentials.DoesNotExist:
            return Response(data={'message': 'Business Central credentials not found in workspace'}, status=status.HTTP_400_BAD_REQUEST)
        except (WrongParamsError, InvalidTokenError):
            if business_central_credentials:
                business_central_credentials.refresh_token = None
                business_central_credentials.is_expired = True
                business_central_credentials.save()
            return Response(data={'message': 'Invalid token or Business Central connection expired'}, status=status.HTTP_400_BAD_REQUEST)
