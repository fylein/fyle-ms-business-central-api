
import logging
import traceback

from dynamics.exceptions.dynamics_exceptions import InvalidTokenError, WrongParamsError

from apps.accounting_exports.models import AccountingExport, Error
from apps.business_central.actions import update_accounting_export_summary
from apps.workspaces.models import BusinessCentralCredentials, FyleCredential
from ms_business_central_api.exceptions import BulkError

logger = logging.getLogger(__name__)
logger.level = logging.INFO


def handle_business_central_error(exception, accounting_export: AccountingExport, export_type: str):
    logger.info(exception.response)
    business_central_error = str(exception.response)
    error_msg = 'Failed to create {0}'.format(export_type)

    error, _ = Error.objects.update_or_create(workspace_id=accounting_export.workspace_id, accounting_export=accounting_export, defaults={'error_title': error_msg, 'type': 'BUSINESS_CENTRAL_ERROR', 'error_detail': business_central_error, 'is_resolved': False})

    error.increase_repetition_count_by_one()

    accounting_export.status = 'FAILED'
    accounting_export.detail = None
    accounting_export.business_central_errors = business_central_error
    accounting_export.save()


def handle_business_central_exceptions():
    def decorator(func):
        def new_fn(*args):

            accounting_export = args[0]

            try:
                return func(*args)
            except (FyleCredential.DoesNotExist):
                logger.info('Fyle credentials not found %s', accounting_export.workspace_id)
                accounting_export.detail = {'message': 'Fyle credentials do not exist in workspace'}
                accounting_export.status = 'FAILED'

                accounting_export.save()

            except BusinessCentralCredentials.DoesNotExist:
                logger.info('Business Central Account not connected / token expired for workspace_id %s / accounting export %s', accounting_export.workspace_id, accounting_export.id)
                detail = {'accounting_export_id': accounting_export.id, 'message': 'Business Central Account not connected / token expired'}
                accounting_export.status = 'FAILED'
                accounting_export.detail = detail

                accounting_export.save()

            except WrongParamsError as exception:
                handle_business_central_error(exception, accounting_export, accounting_export.type)

            except InvalidTokenError as exception:
                logger.info(exception.response)
                business_central_credentials: BusinessCentralCredentials = BusinessCentralCredentials.objects.filter(workspace_id=accounting_export.workspace_id).first()
                if business_central_credentials:
                    business_central_credentials.is_expired = True
                    business_central_credentials.refresh_token = None
                    business_central_credentials.save()

            except BulkError as exception:
                logger.info(exception.response)
                detail = exception.response
                accounting_export.status = 'FAILED'
                accounting_export.detail = detail

                accounting_export.save()

            except Exception as error:
                error = traceback.format_exc()
                accounting_export.detail = {'error': error}
                accounting_export.status = 'FATAL'

                accounting_export.save()
                logger.error('Something unexpected happened workspace_id: %s %s', accounting_export.workspace_id, accounting_export.detail)

            update_accounting_export_summary(accounting_export.workspace_id)

        return new_fn

    return decorator
