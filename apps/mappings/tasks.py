from apps.business_central.utils import BusinessCentralConnector
from apps.workspaces.models import BusinessCentralCredentials


def sync_business_central_attributes(business_central_attribute_type: str, workspace_id: int):
    business_central_credentials: BusinessCentralCredentials = BusinessCentralCredentials.objects.get(workspace_id=workspace_id)

    business_central_connection = BusinessCentralConnector(
        credentials_object=business_central_credentials,
        workspace_id=workspace_id
    )

    sync_functions = {
        'ACCOUNT': business_central_connection.sync_accounts,
        'COMPANY': business_central_connection.sync_companies,
        'LOCATION': business_central_connection.sync_locations,
        'EMPLOYEE': business_central_connection.sync_employees,
        'VENDOR': business_central_connection.sync_vendors,
    }

    sync_function = sync_functions[business_central_attribute_type]
    sync_function()
