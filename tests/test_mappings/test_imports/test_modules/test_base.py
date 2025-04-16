from datetime import datetime, timedelta, timezone
from unittest import mock

from fyle_accounting_mappings.models import CategoryMapping, DestinationAttribute, ExpenseAttribute, Mapping
from fyle_integrations_platform_connector import PlatformConnector

from apps.accounting_exports.models import Error
from apps.mappings.imports.modules.categories import Category
from apps.mappings.imports.modules.projects import Project
from apps.mappings.models import ImportLog
from apps.workspaces.models import FyleCredential, Workspace
from tests.test_mappings.test_imports.test_modules.fixtures import data as destination_attributes_data
from tests.test_mappings.test_imports.test_modules.helpers import get_base_class_instance, get_platform_connection


def test_sync_destination_attributes(
    api_client,
    test_connection,
    create_temp_workspace,
    add_fyle_credentials,
    add_business_central_creds,
    mocker,
):
    workspace_id = 1

    mocker.patch(
        "dynamics.apis.Accounts.get_all",
        return_value=destination_attributes_data["get_account_destination_attributes"],
    )
    mocker.patch(
        "dynamics.apis.Accounts.count",
        return_value=5,
    )

    account_count = DestinationAttribute.objects.filter(
        workspace_id=workspace_id, attribute_type="ACCOUNT"
    ).count()
    assert account_count == 0

    account = Category(workspace_id, "ACCOUNT", None, [])
    account.sync_destination_attributes("ACCOUNT")

    new_account_count = DestinationAttribute.objects.filter(
        workspace_id=workspace_id, attribute_type="ACCOUNT"
    ).count()
    assert new_account_count == 2


def test_sync_expense_atrributes(
    api_client,
    test_connection,
    create_temp_workspace,
    add_fyle_credentials,
    add_business_central_creds,
    mocker,
):
    workspace_id = 1
    fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)
    fyle_credentials.workspace.org_id = "orwimNcVyYsp"
    fyle_credentials.workspace.save()
    platform = PlatformConnector(fyle_credentials=fyle_credentials)

    mocker.patch("fyle.platform.apis.v1.admin.Categories.list_all", return_value=[])

    category_count = ExpenseAttribute.objects.filter(
        workspace_id=workspace_id, attribute_type="CATEGORY"
    ).count()
    assert category_count == 0

    category = Category(workspace_id, "ACCOUNT", None, [])
    category.sync_expense_attributes(platform)

    category_count = ExpenseAttribute.objects.filter(
        workspace_id=workspace_id, attribute_type="CATEGORY"
    ).count()
    assert category_count == 0

    mocker.patch(
        "fyle.platform.apis.v1.admin.Categories.list_all",
        return_value=destination_attributes_data[
            "create_new_auto_create_categories_expense_attributes_0"
        ],
    )
    category.sync_expense_attributes(platform)

    category_count = ExpenseAttribute.objects.filter(
        workspace_id=workspace_id, attribute_type="CATEGORY"
    ).count()
    assert (
        category_count
        == destination_attributes_data[
            "create_new_auto_create_categories_expense_attributes_0"
        ][0]["count"]
    )


def test_remove_duplicates(
    api_client,
    test_connection,
    create_temp_workspace,
    add_fyle_credentials,
    add_business_central_creds,
    add_cost_center_mappings,
):
    attributes = DestinationAttribute.objects.filter(attribute_type="COST_CENTER")

    assert len(attributes) == 6

    for attribute in attributes:
        DestinationAttribute.objects.create(
            attribute_type="COST_CENTER",
            workspace_id=attribute.workspace_id,
            value=attribute.value,
            destination_id="010{0}".format(attribute.destination_id),
        )

    attributes = DestinationAttribute.objects.filter(attribute_type="COST_CENTER")

    assert len(attributes) == 12

    base = get_base_class_instance()

    attributes = base.remove_duplicate_attributes(attributes)
    assert len(attributes) == 2


def test_get_platform_class(
    api_client,
    test_connection,
    create_temp_workspace,
    add_fyle_credentials,
    add_business_central_creds,
):
    base = get_base_class_instance()
    platform = get_platform_connection(1)

    assert base.get_platform_class(platform) == platform.cost_centers

    base = get_base_class_instance(
        workspace_id=1,
        source_field="CATEGORY",
        destination_field="ACCOUNT",
        platform_class_name="categories",
    )
    assert base.get_platform_class(platform) == platform.categories

    base = get_base_class_instance(
        workspace_id=1,
        source_field="COST_CENTER",
        destination_field="DEPARTMENT",
        platform_class_name="cost_centers",
    )
    assert base.get_platform_class(platform) == platform.cost_centers


def test_get_auto_sync_permission(
    api_client,
    test_connection,
    create_temp_workspace,
    add_fyle_credentials,
    add_business_central_creds,
):
    base = get_base_class_instance()

    assert base.get_auto_sync_permission() == False

    base = get_base_class_instance(
        workspace_id=1,
        source_field="CATEGORY",
        destination_field="ACCOUNT",
        platform_class_name="categories",
    )

    assert base.get_auto_sync_permission() == True

    base = get_base_class_instance(
        workspace_id=1,
        source_field="PROJECT",
        destination_field="DEPARTMENT",
        platform_class_name="projects",
    )

    assert base.get_auto_sync_permission() == False


def test_construct_attributes_filter(
    api_client,
    test_connection,
    create_temp_workspace,
    add_fyle_credentials,
    add_business_central_creds,
    add_cost_center_mappings,
):
    base = get_base_class_instance()

    assert base.construct_attributes_filter("PROJECT") == {
        "attribute_type": "PROJECT",
        "workspace_id": 1,
    }

    date_string = "2023-08-06 12:50:05.875029"
    sync_after = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S.%f")

    base = get_base_class_instance(
        workspace_id=1,
        source_field="CATEGORY",
        destination_field="ACCOUNT",
        platform_class_name="categories",
        sync_after=sync_after,
    )

    assert base.construct_attributes_filter("CATEGORY") == {
        "attribute_type": "CATEGORY",
        "workspace_id": 1,
        "updated_at__gte": sync_after,
    }

    paginated_destination_attribute_values = [
        "Mobile App Redesign",
        "Platform APIs",
        "Fyle NetSuite Integration",
        "Fyle Sage Intacct Integration",
        "Support Taxes",
        "T&M Project with Five Tasks",
        "Fixed Fee Project with Five Tasks",
        "General Overhead",
        "General Overhead-Current",
        "Youtube proj",
        "Integrations",
        "Yujiro",
        "Pickle",
    ]

    assert base.construct_attributes_filter(
        "COST_CENTER", paginated_destination_attribute_values
    ) == {
        "attribute_type": "COST_CENTER",
        "workspace_id": 1,
        "updated_at__gte": sync_after,
        "value__in": paginated_destination_attribute_values,
    }


def test_auto_create_destination_attributes(
    api_client,
    test_connection,
    create_temp_workspace,
    add_fyle_credentials,
    add_business_central_creds,
    mocker,
):
    project = Project(1, "EMPLOYEE", None)
    project.sync_after = None

    Workspace.objects.filter(id=1).update(org_id="orqjgyJ21uge")
    # delete all destination attributes, expense attributes and mappings
    Mapping.objects.filter(
        workspace_id=1, source_type="PROJECT", destination_type="EMPLOYEE"
    ).delete()
    DestinationAttribute.objects.filter(
        workspace_id=1, attribute_type="EMPLOYEE"
    ).delete()
    ExpenseAttribute.objects.filter(workspace_id=1, attribute_type="PROJECT").delete()

    # create new case for account import
    with mock.patch("fyle.platform.apis.v1.admin.Projects.list_all") as mock_call:
        mocker.patch(
            "fyle_integrations_platform_connector.apis.Projects.post_bulk",
            return_value=[],
        )
        mocker.patch(
            "dynamics.apis.Employees.get_all",
            return_value=destination_attributes_data[
                "get_employee_destination_attributes_0"
            ],
        )
        mock_call.side_effect = [
            destination_attributes_data[
                "create_new_auto_create_projects_expense_attributes_0"
            ],
            destination_attributes_data[
                "create_new_auto_create_projects_expense_attributes_1"
            ],
        ]

        expense_attributes_count = ExpenseAttribute.objects.filter(
            workspace_id=1, attribute_type="PROJECT"
        ).count()

        assert expense_attributes_count == 0

        mappings_count = Mapping.objects.filter(
            workspace_id=1, source_type="PROJECT", destination_type="EMPLOYEE"
        ).count()

        assert mappings_count == 0

        project.trigger_import()

        expense_attributes_count = ExpenseAttribute.objects.filter(
            workspace_id=1, attribute_type="PROJECT"
        ).count()

        assert expense_attributes_count == 30

        mappings_count = Mapping.objects.filter(
            workspace_id=1, source_type="PROJECT", destination_type="EMPLOYEE"
        ).count()

        assert mappings_count == 2

    # disable case for employee import
    with mock.patch("fyle.platform.apis.v1.admin.Projects.list_all") as mock_call:
        mocker.patch(
            "dynamics.apis.Employees.get_all",
            return_value=destination_attributes_data[
                "create_new_auto_create_employee_destination_attributes_disable_case"
            ],
        )
        mocker.patch(
            "fyle_integrations_platform_connector.apis.Projects.post_bulk",
            return_value=[],
        )
        mock_call.side_effect = [
            destination_attributes_data[
                "create_new_auto_create_projects_expense_attributes_3"
            ],
            destination_attributes_data[
                "create_new_auto_create_projects_expense_attributes_4"
            ],
        ]

        destination_attribute = DestinationAttribute.objects.filter(
            workspace_id=1, value="Ester Henderson"
        ).first()

        assert destination_attribute.active == True

        expense_attribute = ExpenseAttribute.objects.filter(
            workspace_id=1, value="Ester Henderson"
        ).first()

        assert expense_attribute.active == False

        mapping = Mapping.objects.filter(
            destination_id=destination_attribute.id
        ).first()

        pre_run_expense_attribute_disabled_count = ExpenseAttribute.objects.filter(
            workspace_id=1, active=False, attribute_type="PROJECT"
        ).count()

        disabled_expense_attributes_ids = [
            '322907', '322905', '322924', '322923',
            '322922', '320663', '320662', '320661',
            '320660', '320659', '320658', '320657',
            '320656', '320655', '320654', '322927',
            '322926'
        ]

        assert pre_run_expense_attribute_disabled_count == len(disabled_expense_attributes_ids)

        # This confirms that mapping is present and both expense_attribute and destination_attribute are active
        assert mapping.source_id == expense_attribute.id

        project.trigger_import()

        destination_attribute = DestinationAttribute.objects.filter(
            workspace_id=1, value="Annette Hill"
        ).first()

        assert destination_attribute.active == False

        expense_attribute = ExpenseAttribute.objects.filter(
            workspace_id=1, value="Annette Hill"
        ).first()

        assert expense_attribute.active == False

        post_run_expense_attribute_disabled_count = ExpenseAttribute.objects.filter(
            workspace_id=1, active=False, attribute_type="PROJECT"
        ).count()

        assert post_run_expense_attribute_disabled_count == 30

    # not re-enable case for project import
    with mock.patch("fyle.platform.apis.v1.admin.Projects.list_all") as mock_call:
        mocker.patch(
            "dynamics.apis.Employees.get_all",
            return_value=destination_attributes_data[
                "create_new_auto_create_projects_destination_attributes_re_enable_case"
            ],
        )
        mocker.patch(
            "fyle_integrations_platform_connector.apis.Projects.post_bulk",
            return_value=[],
        )
        mock_call.side_effect = [
            destination_attributes_data[
                "create_new_auto_create_projects_expense_attributes_3"
            ],
            destination_attributes_data[
                "create_new_auto_create_projects_expense_attributes_3"
            ],
        ]

        pre_run_destination_attribute_count = DestinationAttribute.objects.filter(
            workspace_id=1, attribute_type="EMPLOYEE", active=False
        ).count()

        assert pre_run_destination_attribute_count == 1

        pre_run_expense_attribute_count = ExpenseAttribute.objects.filter(
            workspace_id=1, attribute_type="PROJECT", active=False
        ).count()

        assert pre_run_expense_attribute_count == 30

        project.trigger_import()

        post_run_destination_attribute_count = DestinationAttribute.objects.filter(
            workspace_id=1, attribute_type="EMPLOYEE", active=False
        ).count()

        assert post_run_destination_attribute_count == 0

        post_run_expense_attribute_count = ExpenseAttribute.objects.filter(
            workspace_id=1, attribute_type="PROJECT", active=False
        ).count()

        assert pre_run_expense_attribute_count == post_run_expense_attribute_count

    # Not creating the schedule part due to time diff
    current_time = datetime.now()
    sync_after = current_time.replace(tzinfo=timezone.utc)
    project.sync_after = sync_after

    import_log = ImportLog.objects.filter(workspace_id=1).first()
    import_log.status = "COMPLETE"
    import_log.attribute_type = "PROJECT"
    import_log.total_batches_count = 10
    import_log.processed_batches_count = 10
    import_log.error_log = []
    import_log.save()

    import_log = ImportLog.objects.filter(workspace_id=1).first()

    response = project.trigger_import()

    import_log_post_run = ImportLog.objects.filter(workspace_id=1).first()

    assert response == None
    assert import_log.status == import_log_post_run.status
    assert import_log.total_batches_count == import_log_post_run.total_batches_count

    # not creating the schedule due to a schedule running already
    project.sync_after = None

    import_log = ImportLog.objects.filter(workspace_id=1).first()
    import_log.status = "IN_PORGRESS"
    import_log.total_batches_count = 8
    import_log.processed_batches_count = 3
    import_log.save()

    response = project.trigger_import()

    assert response == None
    assert import_log.status == "IN_PORGRESS"
    assert import_log.total_batches_count != 0
    assert import_log.processed_batches_count != 0

    # Setting import_log to COMPLETE since there are no destination_attributes
    mocker.patch("fyle.platform.apis.v1.admin.Projects.list_all", return_value=[])
    mocker.patch("dynamics.apis.Employees.get_all", return_value=[])

    Mapping.objects.filter(
        workspace_id=1, source_type="PROJECT", destination_type="EMPLOYEE"
    ).delete()
    DestinationAttribute.objects.filter(
        workspace_id=1, attribute_type="EMPLOYEE"
    ).delete()
    project.sync_after = None

    response = project.trigger_import()

    import_log = ImportLog.objects.filter(
        workspace_id=1, attribute_type="PROJECT"
    ).first()
    assert import_log.status == "COMPLETE"
    assert import_log.total_batches_count == 0
    assert import_log.processed_batches_count == 0
    assert response == None


def test_expense_attributes_sync_after(
    api_client,
    test_connection,
    create_temp_workspace,
    add_fyle_credentials,
    add_business_central_creds,
    add_project_expense_attributes,
):
    project = Project(1, "EMPLOYEE", None)

    current_time = datetime.now() - timedelta(minutes=300)
    sync_after = current_time.replace(tzinfo=timezone.utc)
    project.sync_after = sync_after

    expense_attributes = ExpenseAttribute.objects.filter(
        workspace_id=1, attribute_type="PROJECT"
    )[0:100]

    assert expense_attributes.count() == 100

    paginated_expense_attribute_values = []

    for expense_attribute in expense_attributes:
        expense_attribute.updated_at = datetime.now().replace(tzinfo=timezone.utc)
        expense_attribute.save()
        paginated_expense_attribute_values.append(expense_attribute.value)

    filters = project.construct_attributes_filter(
        "PROJECT", paginated_expense_attribute_values
    )

    expense_attributes = ExpenseAttribute.objects.filter(**filters)

    assert expense_attributes.count() == 100


def test_resolve_expense_attribute_errors(
    api_client,
    test_connection,
    create_temp_workspace,
    add_fyle_credentials,
    add_business_central_creds,
    add_expense_destination_attributes,
):
    workspace_id = 1
    category = Category(1, "ACCOUNT", None, [])

    # deleting all the Error objects
    Error.objects.filter(workspace_id=workspace_id).delete()

    # getting the expense_attribute
    source_category = ExpenseAttribute.objects.filter(
        workspace_id=1, attribute_type="CATEGORY"
    ).first()

    category_mapping_count = CategoryMapping.objects.filter(
        workspace_id=1, source_category_id=source_category.id
    ).count()

    # category mapping is not present
    assert category_mapping_count == 0

    error = Error.objects.create(
        workspace_id=workspace_id,
        expense_attribute=source_category,
        type="CATEGORY_MAPPING",
        error_title=source_category.value,
        error_detail="Category mapping is missing",
        is_resolved=False,
    )

    assert Error.objects.get(id=error.id).is_resolved == False

    destination_attribute = DestinationAttribute.objects.filter(
        workspace_id=1, attribute_type="ACCOUNT"
    ).first()

    # creating the category mapping in bulk mode to avoid setting the is_resolved flag to true by signal
    category_list = []
    category_list.append(
        CategoryMapping(
            workspace_id=1,
            source_category_id=source_category.id,
            destination_account_id=destination_attribute.id,
        )
    )
    CategoryMapping.objects.bulk_create(category_list)

    category.resolve_expense_attribute_errors()
    assert Error.objects.get(id=error.id).is_resolved == True
