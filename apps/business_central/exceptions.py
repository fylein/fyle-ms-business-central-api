
import logging
import traceback

from dynamics.exceptions.dynamics_exceptions import WrongParamsError

from apps.accounting_exports.models import AccountingExport, Error
from apps.business_central.actions import update_last_export_details
from apps.workspaces.models import BusinessCentralCredentials, FyleCredential
from ms_business_central_api.exceptions import BulkError

logger = logging.getLogger(__name__)
logger.level = logging.INFO


def handle_business_central_error(exception, accounting_export: AccountingExport, export_type: str):
    logger.info(exception.response)

    business_central_error = exception.response
    error_msg = 'Failed to create {0}'.format(export_type)

    Error.objects.update_or_create(workspace_id=accounting_export.workspace_id, accounting_export=accounting_export, defaults={'error_title': error_msg, 'type': 'BUSINESS_CENTRAL_ERROR', 'error_detail': business_central_error, 'is_resolved': False})

    accounting_export.status = 'FAILED'
    accounting_export.detail = None
    accounting_export.business_central_errors = business_central_error
    accounting_export.save()


def set_last_export_details(accounting_export: AccountingExport, status, message):
    detail = {'accounting_export_id': accounting_export.id, 'message': '{0}'.format(message)}
    accounting_export.status = status
    accounting_export.detail = detail

    accounting_export.save()


def handle_business_central_exceptions():
    def decorator(func):
        def new_fn(*args):

            accounting_export = args[0]

            try:
                return func(*args)
            except (FyleCredential.DoesNotExist):
                logger.info('Fyle credentials not found %s', accounting_export.workspace_id)
                set_last_export_details(accounting_export, 'FAILED', 'Fyle credentials do not exist in workspace')

            except BusinessCentralCredentials.DoesNotExist:
                logger.info('Business Central Account not connected / token expired for workspace_id %s / accounting export %s', accounting_export.workspace_id, accounting_export.id)
                set_last_export_details(accounting_export, 'FAILED', 'Business Central Account not connected / token expired')

            except WrongParamsError as exception:
                set_last_export_details(exception, accounting_export, 'Purchase Invoice')

            except BulkError as exception:
                logger.info(exception.response)
                set_last_export_details(accounting_export, 'FAILED', exception.response)

            except Exception as error:
                error = traceback.format_exc()
                set_last_export_details(accounting_export, 'FATAL', error)
                logger.error('Something unexpected happened workspace_id: %s %s', accounting_export.workspace_id, accounting_export.detail)

            update_last_export_details(accounting_export.workspace_id)

        return new_fn

    return decorator
