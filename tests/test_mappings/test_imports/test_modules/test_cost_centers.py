from unittest import mock

from fyle_accounting_mappings.models import DestinationAttribute, ExpenseAttribute, Mapping
from fyle_integrations_platform_connector import PlatformConnector

from apps.mappings.imports.modules.cost_centers import CostCenter
from apps.workspaces.models import FyleCredential, Workspace
from tests.test_mappings.test_imports.test_modules.fixtures import data


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
    fyle_credentials.workspace.org_id = "ortL3T2BabCW"
    fyle_credentials.workspace.save()

    platform = PlatformConnector(fyle_credentials=fyle_credentials)

    mocker.patch(
        "fyle.platform.apis.v1beta.admin.CostCenters.list_all", return_value=[]
    )

    cost_center_count = ExpenseAttribute.objects.filter(
        workspace_id=workspace_id, attribute_type="COST_CENTER"
    ).count()
    assert cost_center_count == 0

    category = CostCenter(workspace_id, "LOCATION", None)
    category.sync_expense_attributes(platform)

    cost_center_count = ExpenseAttribute.objects.filter(
        workspace_id=workspace_id, attribute_type="COST_CENTER"
    ).count()
    assert cost_center_count == 0

    mocker.patch(
        "fyle.platform.apis.v1beta.admin.CostCenters.list_all",
        return_value=data["create_new_auto_create_cost_centers_expense_attributes_1"],
    )

    category.sync_expense_attributes(platform)

    cost_center_count = ExpenseAttribute.objects.filter(
        workspace_id=workspace_id, attribute_type="COST_CENTER"
    ).count()
    assert cost_center_count == 7


def test_auto_create_destination_attributes(
    api_client,
    test_connection,
    create_temp_workspace,
    add_fyle_credentials,
    add_business_central_creds,
    mocker,
):
    cost_center = CostCenter(1, "LOCATION", None)
    cost_center.sync_after = None

    Workspace.objects.filter(id=1).update(org_id="ortL3T2BabCW")
    # delete all destination attributes, expense attributes and mappings
    Mapping.objects.filter(
        workspace_id=1, source_type="COST_CENTER", destination_type="LOCATION"
    ).delete()
    DestinationAttribute.objects.filter(
        workspace_id=1, attribute_type="LOCATION"
    ).delete()
    ExpenseAttribute.objects.filter(
        workspace_id=1, attribute_type="COST_CENTER"
    ).delete()

    # create new case for account import
    with mock.patch(
        "fyle.platform.apis.v1beta.admin.CostCenters.list_all"
    ) as mock_call:
        mocker.patch(
            "fyle_integrations_platform_connector.apis.CostCenters.post_bulk",
            return_value=[],
        )
        mocker.patch(
            "dynamics.apis.Locations.get_all",
            return_value=data["get_location_destination_attributes_0"],
        )
        mock_call.side_effect = [
            data["create_new_auto_create_cost_centers_expense_attributes_0"],
            data["create_new_auto_create_cost_centers_expense_attributes_1"],
        ]

        expense_attributes_count = ExpenseAttribute.objects.filter(
            workspace_id=1, attribute_type="COST_CENTER"
        ).count()

        assert expense_attributes_count == 0

        mappings_count = Mapping.objects.filter(
            workspace_id=1, source_type="COST_CENTER", destination_type="LOCATION"
        ).count()

        assert mappings_count == 0

        cost_center.trigger_import()

        expense_attributes_count = ExpenseAttribute.objects.filter(
            workspace_id=1, attribute_type="COST_CENTER"
        ).count()

        assert expense_attributes_count == 9

        mappings_count = Mapping.objects.filter(
            workspace_id=1, source_type="COST_CENTER", destination_type="LOCATION"
        ).count()

        assert mappings_count == 2


def test_construct_fyle_payload(
    api_client,
    test_connection,
    mocker,
    create_temp_workspace,
    add_business_central_creds,
    add_fyle_credentials,
    add_cost_center_mappings,
):
    cost_center = CostCenter(1, "COST_CENTER", None)

    # create new case
    paginated_destination_attributes = DestinationAttribute.objects.filter(
        workspace_id=1, attribute_type="COST_CENTER"
    )

    existing_fyle_attributes_map = {}
    is_auto_sync_status_allowed = cost_center.get_auto_sync_permission()

    fyle_payload = cost_center.construct_fyle_payload(
        paginated_destination_attributes,
        existing_fyle_attributes_map,
        is_auto_sync_status_allowed,
    )

    assert fyle_payload == data["create_fyle_cost_center_payload_create_new_case"]
