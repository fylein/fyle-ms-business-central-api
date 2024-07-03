import base64
import logging
from typing import Dict, List

from dynamics.core.client import Dynamics
from fyle_accounting_mappings.models import DestinationAttribute

from apps.workspaces.models import BusinessCentralCredentials, ExportSetting, Workspace
from ms_business_central_api import settings

logger = logging.getLogger(__name__)
logger.level = logging.INFO


class BusinessCentralConnector:
    """
    Business Central Utility Functions
    """

    def __init__(self, credentials_object: BusinessCentralCredentials, workspace_id: int):
        client_id = settings.BUSINESS_CENTRAL_CLIENT_ID
        client_secret = settings.BUSINESS_CENTRAL_CLIENT_SECRET
        environment = settings.BUSINESS_CENTRAL_ENVIRONMENT if credentials_object.workspace.id != 25 else 'SANDBOX_APRIL2024'
        refresh_token = credentials_object.refresh_token

        business_central_company_id = credentials_object.workspace.business_central_company_id

        self.connection = Dynamics(
            environment=environment,
            client_id=client_id,
            client_secret=client_secret,
            refresh_token=refresh_token,
            company_id=business_central_company_id
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
            value = None
            if 'displayName' in item and item['displayName']:
                value = item['displayName']
            elif 'name' in item and item['name']:
                value = item['name']

            if not value:
                continue
            detail = {field: item[field] for field in field_names}
            if (attribute_type == 'EMPLOYEE' and item.get('status') == 'Active') or (attribute_type in ('LOCATION', 'COMPANY')) or (item.get('blocked') is not None and item.get('blocked') != True):
                active = True
            else:
                active = False
            if attribute_type == 'ACCOUNT':
                if item.get('accountType') != 'Posting' or not item.get('directPosting'):
                    continue
            destination_attributes.append(self._create_destination_attribute(
                attribute_type,
                display_name,
                item['displayName'] if item['displayName'] else item['name'],
                item['number'] if item.get('number') else item['id'],
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
        field_names = []

        self._sync_data(companies, 'COMPANY', 'company', self.workspace_id, field_names)
        return []

    def sync_accounts(self):
        """
        Synchronize accounts from MS Dynamics SDK to your application
        """
        field_names = ['category', 'subCategory', 'accountType', 'directPosting', 'lastModifiedDateTime']

        accounts = self.connection.accounts.get_all()
        self._sync_data(accounts, 'ACCOUNT', 'accounts', self.workspace_id, field_names)
        return []

    def sync_vendors(self):
        """
        Synchronize vendors from MS Dynamics SDK to your application
        """
        field_names = ['email', 'currencyId', 'currencyCode', 'lastModifiedDateTime']

        vendors = self.connection.vendors.get_all()
        self._sync_data(vendors, 'VENDOR', 'vendor', self.workspace_id, field_names)
        return []

    def sync_employees(self):
        """
        Synchronize employees from MS Dynamics SDK to your application
        """
        field_names = ['email', 'personalEmail', 'lastModifiedDateTime']

        employees = self.connection.employees.get_all()
        self._sync_data(employees, 'EMPLOYEE', 'employee', self.workspace_id, field_names)
        return []

    def sync_locations(self):
        """
        Synchronize locations from MS Dynamics SDK to your application
        """
        field_names = ['code', 'city', 'country']

        locations = self.connection.locations.get_all()
        self._sync_data(locations, 'LOCATION', 'location', self.workspace_id, field_names)
        return []

    def get_companies(self):
        """
        Get business central companies
        """
        companies = self.connection.companies.get_all()
        return companies

    def create_journal_entry_folder(self):
        """
        Create default journal entry folder
        """
        journal_entry_folder_list = self.connection.journals.get_all()
        for journal_entry_folder in journal_entry_folder_list:
            if journal_entry_folder['code'] == 'FYLE_JE':
                return journal_entry_folder['id']

        response = self.connection.journals.post({
            'code': 'Fyle_JE',
            'displayName': 'Fyle_JE',
            'templateDisplayName': 'GENERAL'
        })
        return response['id']

    def bulk_post_journal_lineitems(self, payload, accounting_export):
        """
        Bulk post data to MS Dynamics SDK
        """
        workspace = Workspace.objects.get(id=self.workspace_id)
        export_settings = ExportSetting.objects.get(workspace_id=self.workspace_id)

        bulk_post_response = self.connection.journal_line_items.bulk_post(export_settings.journal_entry_folder_id, payload, workspace.business_central_company_id)

        return bulk_post_response

    def post_purchase_invoice(self, purchase_invoice_payload, purchase_invoice_lineitem_payload):
        """
        Post purchase invoice to MS Dynamics SDK
        """
        workspace = Workspace.objects.get(id=self.workspace_id)

        purchase_invoice_response = self.connection.purchase_invoices.post(purchase_invoice_payload)
        bulk_post_response = self.connection.purchase_invoice_line_items.bulk_post(purchase_invoice_response['id'], purchase_invoice_lineitem_payload, workspace.business_central_company_id)

        response = {
            "purchase_invoice_response": purchase_invoice_response,
            "bulk_post_response": bulk_post_response
        }
        return response

    def post_attachments(
        self, ref_type: str, ref_id: str, attachments: List[Dict]
    ) -> List:
        """
        Link attachments to objects Business Central
        :param ref_id: object id
        :param ref_type: type of object
        :param attachments: attachment[dict()]
        """
        responses = []
        if len(attachments):
            for attachment in attachments:
                data = {
                    "parentId": ref_id,
                    "fileName": "{0}_{1}".format(attachment["id"], attachment["name"]),
                    "parentType": ref_type
                }
                post_response = self.connection.attachments.post(data)

                self.connection.attachments.upload(
                    post_response["id"],
                    attachment["content_type"],
                    base64.b64decode(attachment["download_url"])
                )

                responses.append(post_response)

        return post_response
