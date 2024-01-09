import logging
import traceback

from fyle_accounting_mappings.models import CategoryMapping, ExpenseAttribute, Mapping
from fyle_integrations_platform_connector import PlatformConnector

from apps.accounting_exports.models import AccountingExport, Error
from apps.business_central.utils import BusinessCentralConnector
from apps.fyle.models import Expense
from apps.workspaces.models import FyleCredential
from ms_business_central_api.exceptions import BulkError

logger = logging.getLogger(__name__)
logger.level = logging.INFO


def get_filtered_mapping(
    source_field: str, destination_type: str, workspace_id: int, source_value: str, source_id: str) -> Mapping:
    filters = {
        'source_type': source_field,
        'destination_type': destination_type,
        'workspace_id': workspace_id
    }

    if source_id:
        filters['source__source_id'] = source_id
    else:
        filters['source__value'] = source_value

    return Mapping.objects.filter(**filters).first()


def validate_accounting_export(accounting_export: AccountingExport):
    bulk_errors = []
    row = 0

    expenses = accounting_export.expenses.all()

    for lineitem in expenses:
        category = lineitem.category if (lineitem.category == lineitem.sub_category or lineitem.sub_category == None) else '{0} / {1}'.format(
            lineitem.category, lineitem.sub_category)

        category_attribute = ExpenseAttribute.objects.filter(
            value=category,
            workspace_id=accounting_export.workspace_id,
            attribute_type='CATEGORY'
        ).first()

        account = CategoryMapping.objects.filter(
            source_category_id=category_attribute.id,
            workspace_id=accounting_export.workspace_id
        ).first()

        if not account:
            bulk_errors.append({
                'row': row,
                'accounting_export_id': accounting_export.id,
                'value': category,
                'type': 'Category Mapping',
                'message': 'Category Mapping not found'
            })

            if category_attribute:
                Error.objects.update_or_create(
                    workspace_id=accounting_export.workspace_id,
                    expense_attribute=category_attribute,
                    defaults={
                        'type': 'CATEGORY_MAPPING',
                        'error_title': category_attribute.value,
                        'error_detail': 'Category mapping is missing',
                        'is_resolved': False
                    }
                )

        row = row + 1

    if bulk_errors:
        raise BulkError('Mappings are missing', bulk_errors)


def resolve_errors_for_exported_accounting_export(accounting_export: AccountingExport):
    """
    Resolve errors for exported accounting export
    :param accounting_export: Accounting Export
    """
    Error.objects.filter(workspace_id=accounting_export.workspace_id, accounting_export=accounting_export, is_resolved=False).update(is_resolved=True)


def load_attachments(
    business_central_connection: BusinessCentralConnector,
    ref_id: str,
    ref_type: str,
    expense: Expense,
    accounting_export: AccountingExport,
):
    """
    Get attachments from fyle
    :param business_central_connection: Business Central Connection
    :param ref_id: object id
    :param ref_type: type of object
    :param expense_group: Expense group
    """
    try:
        fyle_credentials = FyleCredential.objects.get(
            workspace_id=accounting_export.workspace_id
        )
        platform = PlatformConnector(fyle_credentials)

        files_list = []

        if expense.file_ids and len(expense.file_ids):
            for file_id in expense.file_ids:
                if file_id:
                    file_object = {"id": file_id}
                    files_list.append(file_object)

            if files_list:
                attachments = platform.files.bulk_generate_file_urls(files_list)

            business_central_connection.post_attachments(ref_id, ref_type, attachments)

    except Exception:
        error = traceback.format_exc()
        logger.info(
            "Attachment failed for accounting export id %s / workspace id %s \n Error: %s",
            accounting_export.id,
            accounting_export.workspace_id,
            {"error": error},
        )
