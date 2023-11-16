import logging
from django.db.models import Q
from datetime import datetime
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import status

from fyle_accounting_mappings.models import DestinationAttribute

from apps.workspaces.models import Workspace, BusinessCentralCredentials
from apps.business_central.helpers import sync_dimensions, check_interval_and_sync_dimension


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
            business_central_credentials = BusinessCentralCredentials.objects.get(
                workspace_id=workspace.id
            )

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
