
import logging
from datetime import datetime, timezone

from django.utils.module_loading import import_string

from apps.workspaces.models import BusinessCentralCredentials, Workspace

logger = logging.getLogger(__name__)
logger.level = logging.INFO


# Import your Workspace and BusinessCentralCredentials models here
# Also, make sure you have 'logger' defined and imported from a logging module
def check_interval_and_sync_dimension(workspace: Workspace, business_central_credential: BusinessCentralCredentials) -> bool:
    """
    Check the synchronization interval and trigger dimension synchronization if needed.

    :param workspace: Workspace Instance
    :param business_central_credential: BusinessCentralCredentials Instance

    :return: True if synchronization is triggered, False if not
    """

    if workspace.destination_synced_at:
        # Calculate the time interval since the last destination sync
        time_interval = datetime.now(timezone.utc) - workspace.destination_synced_at

    if workspace.destination_synced_at is None or time_interval.days > 0:
        # If destination_synced_at is None or the time interval is greater than 0 days, trigger synchronization
        sync_dimensions(business_central_credential, workspace.id)
        return True

    return False


def sync_dimensions(business_central_credential: BusinessCentralCredentials, workspace_id: int) -> None:
    """
    Synchronize various dimensions with Business Central using the provided credentials.

    :param business_central_credential: BusinessCentralCredentials Instance
    :param workspace_id: ID of the workspace

    This function syncs dimensions like accounts, vendors, commitments, jobs, categories, and cost codes.
    """

    # Initialize the Business Central connection using the provided credentials and workspace ID
    business_central_connection = import_string('apps.business_central.utils.BusinessCentralConnector')(business_central_credential, workspace_id)

    # List of dimensions to sync
    dimensions = ['companies', 'accounts', 'vendors', 'employees', 'locations', 'bank_accounts', 'dimensions']

    for dimension in dimensions:
        try:
            # Dynamically call the sync method based on the dimension
            sync = getattr(business_central_connection, 'sync_{}'.format(dimension))
            sync()
        except Exception as exception:
            # Log any exceptions that occur during synchronization
            logger.info(exception)
