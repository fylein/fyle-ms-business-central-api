from datetime import datetime, timezone
from unittest import mock

from fyle_accounting_mappings.models import DestinationAttribute, ExpenseAttribute, Mapping

from apps.mappings.imports.modules.projects import Project
from apps.mappings.models import ImportLog
from apps.workspaces.models import Workspace
from tests.test_mappings.test_imports.test_modules.fixtures import data


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
    with mock.patch("fyle.platform.apis.v1beta.admin.Projects.list_all") as mock_call:
        mocker.patch(
            "fyle_integrations_platform_connector.apis.Projects.post_bulk",
            return_value=[],
        )
        mocker.patch(
            "dynamics.apis.Employees.get_all",
            return_value=data["get_employee_destination_attributes_0"],
        )
        mock_call.side_effect = [
            data["create_new_auto_create_projects_expense_attributes_0"],
            data["create_new_auto_create_projects_expense_attributes_1"],
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
    with mock.patch("fyle.platform.apis.v1beta.admin.Projects.list_all") as mock_call:
        mocker.patch(
            "dynamics.apis.Employees.get_all",
            return_value=data[
                "create_new_auto_create_employee_destination_attributes_disable_case"
            ],
        )
        mocker.patch(
            "fyle_integrations_platform_connector.apis.Projects.post_bulk",
            return_value=[],
        )
        mock_call.side_effect = [
            data["create_new_auto_create_projects_expense_attributes_3"],
            data["create_new_auto_create_projects_expense_attributes_4"],
        ]

        destination_attribute = DestinationAttribute.objects.filter(
            workspace_id=1, value="Ester Henderson"
        ).first()

        assert destination_attribute.active == True

        expense_attribute = ExpenseAttribute.objects.filter(
            workspace_id=1, value="Ester Henderson"
        ).first()

        assert expense_attribute.active == True

        mapping = Mapping.objects.filter(
            destination_id=destination_attribute.id
        ).first()

        pre_run_expense_attribute_disabled_count = ExpenseAttribute.objects.filter(
            workspace_id=1, active=False, attribute_type="PROJECT"
        ).count()

        assert pre_run_expense_attribute_disabled_count == 2

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

        assert (
            post_run_expense_attribute_disabled_count
            == pre_run_expense_attribute_disabled_count
            + data["create_new_auto_create_projects_expense_attributes_4"][0]["count"]
        )

    # not re-enable case for project import
    with mock.patch("fyle.platform.apis.v1beta.admin.Projects.list_all") as mock_call:
        mocker.patch(
            "dynamics.apis.Employees.get_all",
            return_value=data[
                "create_new_auto_create_projects_destination_attributes_re_enable_case"
            ],
        )
        mocker.patch(
            "fyle_integrations_platform_connector.apis.Projects.post_bulk",
            return_value=[],
        )
        mock_call.side_effect = [
            data["create_new_auto_create_projects_expense_attributes_3"],
            data["create_new_auto_create_projects_expense_attributes_3"],
        ]

        pre_run_destination_attribute_count = DestinationAttribute.objects.filter(
            workspace_id=1, attribute_type="EMPLOYEE", active=False
        ).count()

        assert pre_run_destination_attribute_count == 1

        pre_run_expense_attribute_count = ExpenseAttribute.objects.filter(
            workspace_id=1, attribute_type="PROJECT", active=False
        ).count()

        assert pre_run_expense_attribute_count == 4

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
    mocker.patch("fyle.platform.apis.v1beta.admin.Projects.list_all", return_value=[])
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


def test_construct_fyle_payload(
    api_client,
    test_connection,
    mocker,
    create_temp_workspace,
    add_business_central_creds,
    add_fyle_credentials,
    add_project_mappings,
):
    project = Project(1, "PROJECT", None)

    # create new case
    paginated_destination_attributes = DestinationAttribute.objects.filter(
        workspace_id=1, attribute_type="PROJECT"
    )

    existing_fyle_attributes_map = {}
    is_auto_sync_status_allowed = project.get_auto_sync_permission()

    fyle_payload = project.construct_fyle_payload(
        paginated_destination_attributes,
        existing_fyle_attributes_map,
        is_auto_sync_status_allowed,
    )

    assert fyle_payload == data["create_fyle_project_payload_create_new_case"]

    # disable case
    DestinationAttribute.objects.filter(
        workspace_id=1, attribute_type="PROJECT", value__in=["Platform APIs"]
    ).update(active=False)

    paginated_destination_attributes = DestinationAttribute.objects.filter(
        workspace_id=1, attribute_type="PROJECT"
    )

    paginated_destination_attribute_values = [
        attribute.value for attribute in paginated_destination_attributes
    ]

    existing_fyle_attributes_map = project.get_existing_fyle_attributes(
        paginated_destination_attribute_values
    )

    fyle_payload = project.construct_fyle_payload(
        paginated_destination_attributes, existing_fyle_attributes_map, True
    )

    assert fyle_payload == data["create_fyle_project_payload_create_disable_case"]
