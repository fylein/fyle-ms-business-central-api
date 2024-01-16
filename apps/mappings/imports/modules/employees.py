from datetime import datetime
from typing import List

from fyle_accounting_mappings.models import DestinationAttribute, EmployeeMapping, ExpenseAttribute
from fyle_integrations_platform_connector import PlatformConnector

from apps.mappings.exceptions import handle_import_exceptions
from apps.mappings.imports.modules.base import Base
from apps.mappings.models import ImportLog
from apps.workspaces.models import FyleCredential


class Employee(Base):
    """
    Class for ExepenseCustomField module
    """
    def __init__(self, workspace_id: int, destination_field: str, sync_after: datetime):
        super().__init__(
            workspace_id=workspace_id,
            source_field='EMPLOYEE',
            destination_field=destination_field,
            platform_class_name='employees',
            sync_after=sync_after
        )

    def trigger_import(self):
        """
        Trigger import for ExepenseCustomField module
        """
        self.check_import_log_and_start_import()

    def get_existing_source_and_mappings(self, destination_type: str, workspace_id: int):
        existing_mappings = EmployeeMapping.objects.filter(workspace_id=workspace_id).all()

        existing_source_ids = []
        for mapping in existing_mappings:
            destination = None
            if destination_type == 'EMPLOYEE':
                destination = mapping.destination_employee
            elif destination_type == 'VENDOR':
                destination = mapping.destination_vendor
            elif destination_type == 'CREDIT_CARD_ACCOUNT':
                destination = mapping.destination_card_account

            if destination:
                existing_source_ids.append(mapping.source_employee.id)

        return existing_source_ids, existing_mappings

    def check_exact_matches(self, source_attribute: ExpenseAttribute, destination_id_value_map: dict, destination_type: str):
        """
        Check if the source attribute matches with the destination attribute
        :param employee_mapping_preference: Employee Mapping Preference
        :param source_attribute: Source Attribute
        :param destination_id_value_map: Destination ID Value Map
        :param destination_type: Destination Type
        :return: Destination Column and value if exact match found
        """
        source_value = ''
        destination = {}

        source_value = source_attribute.value

        # Handling employee_code or full_name null case
        if not source_value:
            source_value = ''

        # Checking exact match
        if source_value.lower() in destination_id_value_map:
            if destination_type == 'EMPLOYEE':
                destination['destination_employee_id'] = destination_id_value_map[source_value.lower()]
            elif destination_type == 'VENDOR':
                destination['destination_vendor_id'] = destination_id_value_map[source_value.lower()]
            elif destination_type == 'CREDIT_CARD_ACCOUNT':
                destination['destination_card_account_id'] = destination_id_value_map[source_value.lower()]

        return destination

    def construct_mapping_payload(self, employee_source_attributes: List[ExpenseAttribute], destination_id_value_map: dict, destination_type: str, workspace_id: int):
        """
        Construct mapping payload
        :param employee_source_attributes: Employee Source Attributes
        :param employee_mapping_preference: Employee Mapping Preference
        :param destination_id_value_map: Destination ID Value Map
        :param destination_type: Destination Type
        :param workspace_id: Workspace ID
        :return: mapping_creation_batch, mapping_updation_batch, update_key
        """
        existing_source_ids, existing_mappings = self.get_existing_source_and_mappings(destination_type, workspace_id)

        mapping_creation_batch = []
        mapping_updation_batch = []
        update_key = None
        existing_mappings_map = {mapping.source_employee_id: mapping.id for mapping in existing_mappings}

        for source_attribute in employee_source_attributes:
            # Ignoring already present mappings
            if source_attribute.id not in existing_source_ids:
                destination = self.check_exact_matches(source_attribute, destination_id_value_map, destination_type)
                if destination:
                    update_key = list(destination.keys())[0]
                    if source_attribute.id in existing_mappings_map:
                        # If employee mapping row exists, then update it
                        mapping_updation_batch.append(EmployeeMapping(id=existing_mappings_map[source_attribute.id], source_employee=source_attribute, **destination))
                    else:
                        # If employee mapping row does not exist, then create it
                        mapping_creation_batch.append(EmployeeMapping(source_employee_id=source_attribute.id, workspace_id=workspace_id, **destination))

        return mapping_creation_batch, mapping_updation_batch, update_key

    def create_mappings_and_update_flag(self, mapping_creation_batch: List[EmployeeMapping], mapping_updation_batch: List[EmployeeMapping], update_key: str):
        """
        Create Mappings and Update Flag
        :param mapping_creation_batch: Mapping Creation Batch
        :param mapping_updation_batch: Mapping Updation Batch
        :param update_key: Update Key
        :return: created mappings
        """
        mappings = []

        if mapping_creation_batch:
            created_mappings = EmployeeMapping.objects.bulk_create(mapping_creation_batch, batch_size=50)
            mappings.extend(created_mappings)

        if mapping_updation_batch:
            EmployeeMapping.objects.bulk_update(mapping_updation_batch, fields=[update_key], batch_size=50)
            for mapping in mapping_updation_batch:
                mappings.append(mapping)

        expense_attributes_to_be_updated = []

        for mapping in mappings:
            expense_attributes_to_be_updated.append(ExpenseAttribute(id=mapping.source_employee.id, auto_mapped=True))

        if expense_attributes_to_be_updated:
            ExpenseAttribute.objects.bulk_update(expense_attributes_to_be_updated, fields=['auto_mapped'], batch_size=50)

        return mappings

    def auto_map_employees(self, destination_type: str, workspace_id: int, import_log: ImportLog):
        """
        Auto map employees
        :param destination_type: Destination Type of mappings
        :param employee_mapping_preference: Employee Mapping Preference
        :param workspace_id: Workspace ID
        """
        # Filtering only not mapped destination attributes
        employee_destination_attributes = DestinationAttribute.objects.filter(attribute_type=destination_type, workspace_id=workspace_id).all()

        destination_id_value_map = {}
        for destination_employee in employee_destination_attributes:
            value_to_be_appended = None
            value_to_be_appended = destination_employee.detail['email'].replace('*', '')

            if value_to_be_appended:
                destination_id_value_map[value_to_be_appended.lower()] = destination_employee.id

        filters = {'attribute_type': 'EMPLOYEE', 'workspace_id': workspace_id}

        if destination_type == 'VENDOR':
            filters['employeemapping__destination_vendor__isnull'] = True
        else:
            filters['employeemapping__destination_employee__isnull'] = True

        employee_source_attributes_count = ExpenseAttribute.objects.filter(**filters).count()
        page_size = 200
        employee_source_attributes = []

        for offset in range(0, employee_source_attributes_count, page_size):
            limit = offset + page_size
            paginated_employee_source_attributes = ExpenseAttribute.objects.filter(**filters)[offset:limit]
            employee_source_attributes.extend(paginated_employee_source_attributes)

        mapping_creation_batch, mapping_updation_batch, update_key = self.construct_mapping_payload(employee_source_attributes, destination_id_value_map, destination_type, workspace_id)
        self.create_mappings_and_update_flag(mapping_creation_batch, mapping_updation_batch, update_key)

        import_log.status = 'COMPLETE'
        import_log.last_successful_run_at = datetime.now()
        import_log.error_log = []
        import_log.total_batches_count = 0
        import_log.processed_batches_count = 0
        import_log.save()
        return

    @handle_import_exceptions
    def import_destination_attribute_to_fyle(self, import_log: ImportLog):
        """
        Import destiantion_attributes field to Fyle and Auto Create Mappings
        :param import_log: ImportLog object
        """

        fyle_credentials = FyleCredential.objects.get(workspace_id=self.workspace_id)
        platform = PlatformConnector(fyle_credentials=fyle_credentials)

        self.sync_destination_attributes(self.destination_field)

        self.sync_expense_attributes(platform)

        self.auto_map_employees(self.destination_field, self.workspace_id, import_log)

        self.resolve_expense_attribute_errors()
