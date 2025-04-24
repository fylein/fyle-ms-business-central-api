from unittest import mock

from fyle_accounting_mappings.models import DestinationAttribute, ExpenseAttribute, Mapping
from fyle_integrations_platform_connector import PlatformConnector

from apps.mappings.imports.modules.expense_custom_fields import ExpenseCustomField
from apps.workspaces.models import FyleCredential
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
    fyle_credentials.workspace.org_id = "orqjgyJ21uge"
    fyle_credentials.workspace.save()
    platform = PlatformConnector(fyle_credentials=fyle_credentials)

    expense_attribute_count = ExpenseAttribute.objects.filter(
        workspace_id=workspace_id, attribute_type="LUKE"
    ).count()
    assert expense_attribute_count == 0

    mocker.patch(
        "fyle.platform.apis.v1.admin.ExpenseFields.list_all", return_value=[]
    )

    expense_custom_field = ExpenseCustomField(workspace_id, "LUKE", "CLASS", None)
    expense_custom_field.sync_expense_attributes(platform)

    expense_attribute_count = ExpenseAttribute.objects.filter(
        workspace_id=workspace_id, attribute_type="LUKE"
    ).count()
    assert expense_attribute_count == 0

    mocker.patch(
        "fyle.platform.apis.v1.admin.ExpenseFields.list_all",
        return_value=data[
            "create_new_auto_create_expense_custom_fields_expense_attributes_0"
        ],
    )

    expense_custom_field.sync_expense_attributes(platform)

    expense_attribute_count = ExpenseAttribute.objects.filter(
        workspace_id=workspace_id, attribute_type="LUKE"
    ).count()
    assert expense_attribute_count == 21


def test_auto_create_destination_attributes(
    api_client,
    test_connection,
    create_temp_workspace,
    add_fyle_credentials,
    add_business_central_creds,
    mocker,
):
    workspace_id = 1
    fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)
    fyle_credentials.workspace.org_id = "orqjgyJ21uge"
    fyle_credentials.workspace.save()

    expense_custom_field = ExpenseCustomField(1, "LUKE", "LOCATION", None)
    expense_custom_field.sync_after = None

    # delete all destination attributes, expense attributes and mappings
    Mapping.objects.filter(
        workspace_id=1, source_type="LUKE", destination_type="LOCATION"
    ).delete()
    DestinationAttribute.objects.filter(
        workspace_id=1, attribute_type="LOCATION"
    ).delete()
    ExpenseAttribute.objects.filter(workspace_id=1, attribute_type="LUKE").delete()

    # create new case for projects import
    with mock.patch(
        "fyle.platform.apis.v1.admin.ExpenseFields.list_all"
    ) as mock_call:
        mocker.patch(
            "fyle_integrations_platform_connector.apis.ExpenseCustomFields.post",
            return_value=[],
        )
        mocker.patch(
            "dynamics.apis.Locations.count",
            return_value=5,
        )
        mocker.patch(
            "dynamics.apis.Locations.get_all",
            return_value=data["get_location_destination_attributes_2"],
        )
        mock_call.side_effect = [
            data["create_new_auto_create_expense_custom_fields_expense_attributes_0"],
        ]

        expense_attributes_count = ExpenseAttribute.objects.filter(
            workspace_id=1, attribute_type="LUKE"
        ).count()

        assert expense_attributes_count == 0

        mappings_count = Mapping.objects.filter(
            workspace_id=1, source_type="LUKE", destination_type="LOCATION"
        ).count()

        assert mappings_count == 0

        expense_custom_field.trigger_import()

        expense_attributes_count = ExpenseAttribute.objects.filter(
            workspace_id=1, attribute_type="LUKE"
        ).count()

        assert expense_attributes_count == 21

        destination_attributes_count = DestinationAttribute.objects.filter(
            workspace_id=1, attribute_type="LOCATION"
        ).count()

        assert destination_attributes_count == 2

        mappings_count = Mapping.objects.filter(
            workspace_id=1, source_type="LUKE", destination_type="LOCATION"
        ).count()

        assert mappings_count == 2

    # create new expense_custom_field mapping for sub-sequent run (we will be adding 2 new LOCATION)
    with mock.patch(
        "fyle.platform.apis.v1.admin.ExpenseFields.list_all"
    ) as mock_call:
        mocker.patch(
            "fyle_integrations_platform_connector.apis.ExpenseCustomFields.post",
            return_value=[],
        )
        mocker.patch(
            "fyle_integrations_platform_connector.apis.ExpenseCustomFields.get_by_id",
            return_value=data["create_new_auto_create_expense_custom_fields_get_by_id"],
        )
        mocker.patch(
            "dynamics.apis.Locations.count",
            return_value=5,
        )
        mocker.patch(
            "dynamics.apis.Locations.get_all",
            return_value=data["get_location_destination_attributes_3"],
        )
        mock_call.side_effect = [
            data["create_new_auto_create_expense_custom_fields_expense_attributes_1"],
        ]

        expense_attributes_count = ExpenseAttribute.objects.filter(
            workspace_id=1, attribute_type="LUKE"
        ).count()

        assert expense_attributes_count == 21

        mappings_count = Mapping.objects.filter(
            workspace_id=1, source_type="LUKE", destination_type="LOCATION"
        ).count()

        assert mappings_count == 2

        expense_custom_field.trigger_import()

        expense_attributes_count = ExpenseAttribute.objects.filter(
            workspace_id=1, attribute_type="LUKE"
        ).count()

        assert expense_attributes_count == 21 + 2

        mappings_count = Mapping.objects.filter(
            workspace_id=1, source_type="LUKE", destination_type="LOCATION"
        ).count()

        assert mappings_count == 4


def test_construct_fyle_expense_custom_field_payload(
    api_client,
    test_connection,
    create_temp_workspace,
    add_fyle_credentials,
    add_business_central_creds,
    mocker,
):
    expense_custom_field = ExpenseCustomField(1, "LUKE", "LOCATION", None)
    expense_custom_field.sync_after = None
    fyle_credentials = FyleCredential.objects.get(workspace_id=1)
    platform = PlatformConnector(fyle_credentials=fyle_credentials)

    # create new case
    paginated_destination_attributes = DestinationAttribute.objects.filter(
        workspace_id=1, attribute_type="LOCATION"
    )

    fyle_payload = expense_custom_field.construct_fyle_expense_custom_field_payload(
        paginated_destination_attributes, platform
    )

    assert (
        fyle_payload
        == data["create_fyle_expense_custom_fields_payload_create_new_case"]
    )
