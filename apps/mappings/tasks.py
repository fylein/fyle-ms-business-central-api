import logging
from datetime import datetime
from typing import List

from django_q.models import Schedule
from dynamics.exceptions.dynamics_exceptions import InvalidTokenError, NoPrivilegeError
from fyle.platform.exceptions import InvalidTokenError as FyleInvalidTokenError
from fyle_accounting_mappings.helpers import EmployeesAutoMappingHelper
from fyle_accounting_mappings.models import EmployeeMapping
from fyle_integrations_platform_connector import PlatformConnector

from apps.accounting_exports.models import Error
from apps.business_central.utils import BusinessCentralConnector
from apps.workspaces.models import BusinessCentralCredentials, ExportSetting, FyleCredential

logger = logging.getLogger(__name__)
logger.level = logging.INFO


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


def get_mapped_attributes_ids(source_attribute_type: str, destination_attribute_type: str, errored_attribute_ids: List[int]):

    mapped_attribute_ids = []

    if source_attribute_type == "EMPLOYEE":
        params = {
            'source_employee_id__in': errored_attribute_ids,
        }

        if destination_attribute_type == "EMPLOYEE":
            params['destination_employee_id__isnull'] = False
        else:
            params['destination_vendor_id__isnull'] = False
        mapped_attribute_ids: List[int] = EmployeeMapping.objects.filter(
            **params
        ).values_list('source_employee_id', flat=True)

    return mapped_attribute_ids


def resolve_expense_attribute_errors(
    source_attribute_type: str, workspace_id: int, destination_attribute_type: str = None):
    """
    Resolve Expense Attribute Errors
    :return: None
    """
    errored_attribute_ids: List[int] = Error.objects.filter(
        is_resolved=False,
        workspace_id=workspace_id,
        type='{}_MAPPING'.format(source_attribute_type)
    ).values_list('expense_attribute_id', flat=True)

    if errored_attribute_ids:
        mapped_attribute_ids = get_mapped_attributes_ids(source_attribute_type, destination_attribute_type, errored_attribute_ids)

        if mapped_attribute_ids:
            Error.objects.filter(expense_attribute_id__in=mapped_attribute_ids).update(is_resolved=True)


def async_auto_map_employees(workspace_id: int):
    export_settings: ExportSetting = ExportSetting.objects.get(workspace_id=workspace_id)

    employee_mapping_preference = export_settings.auto_map_employees

    destination_type = export_settings.employee_field_mapping

    fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)

    try:
        platform = PlatformConnector(fyle_credentials=fyle_credentials)
        business_central_credentials = BusinessCentralCredentials.objects.get(workspace_id=workspace_id)
        business_central_connection = BusinessCentralConnector(
            credentials_object=business_central_credentials, workspace_id=workspace_id)

        platform.employees.sync()
        if destination_type == 'EMPLOYEE':
            business_central_connection.sync_employees()
        else:
            business_central_connection.sync_vendors()

        EmployeesAutoMappingHelper(workspace_id, destination_type, employee_mapping_preference).reimburse_mapping()
        resolve_expense_attribute_errors(
            source_attribute_type="EMPLOYEE",
            workspace_id=workspace_id,
            destination_attribute_type=destination_type,
        )
    except (BusinessCentralCredentials.DoesNotExist, InvalidTokenError):
        logger.info('Invalid Token or Sage Intacct Credentials does not exist - %s', workspace_id)

    except FyleInvalidTokenError:
        logger.info('Invalid Token for fyle')

    except NoPrivilegeError:
        logger.info('Insufficient permission to access the requested module')


def schedule_auto_map_employees(employee_mapping_preference: str, workspace_id: int):
    if employee_mapping_preference:
        start_datetime = datetime.now()

        schedule, _ = Schedule.objects.update_or_create(
            func='apps.mappings.tasks.async_auto_map_employees',
            args='{}'.format(workspace_id),
            defaults={
                'schedule_type': Schedule.MINUTES,
                'minutes': 24 * 60,
                'next_run': start_datetime
            }
        )
    else:
        schedule: Schedule = Schedule.objects.filter(
            func='apps.mappings.tasks.async_auto_map_employees',
            args='{}'.format(workspace_id)
        ).first()

        if schedule:
            schedule.delete()
