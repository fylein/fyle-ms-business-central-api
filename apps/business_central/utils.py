from dynamics.core.client import Dynamics
from fyle_accounting_mappings.models import DestinationAttribute

from apps.workspaces.models import BusinessCentralCredentials, Workspace
from ms_business_central_api import settings


class BusinessCentralConnector:
    """
    Business Central Utility Functions
    """

    def __init__(self, credentials_object: BusinessCentralCredentials, workspace_id: int):
        client_id = settings.BUSINESS_CENTRAL_CLIENT_ID
        client_secret = settings.BUSINESS_CENTRAL_CLIENT_SECRET
        environment = settings.BUSINESS_CENTRAL_ENVIRONMENT
        refresh_token = credentials_object.refresh_token

        self.connection = Dynamics(
            environment=environment,
            client_id=client_id,
            client_secret=client_secret,
            refresh_token=refresh_token,
        )

        self.workspace_id = workspace_id

        credentials_object.refresh_token = self.connection.refresh_token
        credentials_object.save()

    def _create_destination_attribute(self, attribute_type, display_name, value, destination_id, active, detail):
        """
        Create a destination attribute object
        :param attribute_type: Type of the attribute
        :param display_name: Display name for the attribute
        :param value: Value of the attribute
        :param destination_id: ID of the destination
        :param active: Whether the attribute is active
        :param detail: Details related to the attribute
        :return: A destination attribute dictionary
        """
        return {
            'attribute_type': attribute_type,
            'display_name': display_name,
            'value': value,
            'destination_id': destination_id,
            'active': active,
            'detail': detail
        }

    def _sync_data(self, data, attribute_type, display_name, workspace_id, field_names):
        """
        Synchronize data from MS Dynamics SDK to your application
        :param data: Data to synchronize
        :param attribute_type: Type of the attribute
        :param display_name: Display name for the data
        :param workspace_id: ID of the workspace
        :param field_names: Names of fields to include in detail
        """

        destination_attributes = []
        for item in data:
            detail = {field: item[field] for field in field_names}
            if (attribute_type == 'EMPLOYEE' and item['status'] == 'Active') or attribute_type == 'LOCATION' or item['blocked'] != True:
                active = True
            else:
                active = False
            destination_attributes.append(self._create_destination_attribute(
                attribute_type,
                display_name,
                item['displayName'],
                item['id'],
                active,
                detail
            ))
        DestinationAttribute.bulk_create_or_update_destination_attributes(
            destination_attributes, attribute_type, workspace_id, True)

    def sync_companies(self):
        """
        sync business central companies
        """
        companies = self.connection.companies.get_all()

        self._sync_data(companies, 'COMPANY', 'company', self.workspace_id)
        return []

    def sync_accounts(self):
        """
        Synchronize accounts from MS Dynamics SDK to your application
        """
        workspace = Workspace.objects.get(id=self.workspace_id)
        self.connection.company_id = workspace.business_central_company_id
        field_names = ['category', 'subCategory', 'accountType', 'directPosting', 'lastModifiedDateTime']

        accounts = self.connection.accounts.get_all()
        self._sync_data(accounts, 'ACCOUNT', 'accounts', self.workspace_id, field_names)
        return []

    def sync_vendors(self):
        """
        Synchronize vendors from MS Dynamics SDK to your application
        """
        workspace = Workspace.objects.get(id=self.workspace_id)
        self.connection.company_id = workspace.business_central_company_id
        field_names = ['email', 'currencyId', 'currencyCode', 'lastModifiedDateTime']

        vendors = self.connection.vendors.get_all()
        self._sync_data(vendors, 'VENDOR', 'vendor', self.workspace_id, field_names)
        return []

    def sync_employees(self):
        """
        Synchronize employees from MS Dynamics SDK to your application
        """
        workspace = Workspace.objects.get(id=self.workspace_id)
        self.connection.company_id = workspace.business_central_company_id
        field_names = ['email', 'email', 'personalEmail', 'lastModifiedDateTime']

        employees = self.connection.employees.get_all()
        self._sync_data(employees, 'EMPLOYEE', 'employee', self.workspace_id, field_names)
        return []

    def sync_locations(self):
        """
        Synchronize locations from MS Dynamics SDK to your application
        """
        workspace = Workspace.objects.get(id=self.workspace_id)
        self.connection.company_id = workspace.business_central_company_id
        field_names = ['code', 'city', 'country']

        locations = self.connection.locations.get_all()
        self._sync_data(locations, 'LOCATION', 'location', self.workspace_id, field_names)
        return []
