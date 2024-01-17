from apps.mappings.imports.modules.categories import Category
from apps.mappings.imports.modules.cost_centers import CostCenter
from apps.mappings.imports.modules.employees import Employee
from apps.mappings.imports.modules.expense_custom_fields import ExpenseCustomField
from apps.mappings.imports.modules.merchants import Merchant
from apps.mappings.imports.modules.projects import Project
from apps.mappings.models import ImportLog

SOURCE_FIELD_CLASS_MAP = {
    'CATEGORY': Category,
    'MERCHANT': Merchant,
    'COST_CENTER': CostCenter,
    'PROJECT': Project,
    'EMPLOYEE': Employee,
}


def trigger_import_via_schedule(workspace_id: int, destination_field: str, source_field: str, is_custom: bool = False):
    """
    Trigger import via schedule
    :param workspace_id: Workspace id
    :param destination_field: Destination field
    :param source_field: Type of attribute (e.g. 'CATEGORY', 'MERCHANT', 'COST_CENTER', 'PROJECT')
    """
    import_log = ImportLog.objects.filter(workspace_id=workspace_id, attribute_type=source_field).first()
    sync_after = import_log.last_successful_run_at if import_log else None

    if is_custom:
        item = ExpenseCustomField(workspace_id, source_field, destination_field, sync_after)
        item.trigger_import()
    else:
        module_class = SOURCE_FIELD_CLASS_MAP[source_field]
        item = module_class(workspace_id, destination_field, sync_after)
        item.trigger_import()
