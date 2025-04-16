from unittest import mock

from fyle_accounting_mappings.models import CategoryMapping, DestinationAttribute, ExpenseAttribute, Mapping
from fyle_integrations_platform_connector import PlatformConnector

from apps.mappings.imports.modules.categories import Category
from apps.workspaces.models import FyleCredential, Workspace
from tests.test_mappings.test_imports.test_modules.fixtures import data as destination_attributes_data


def test_sync_destination_attributes_categories(
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

    category = Category(workspace_id, "ACCOUNT", None, [])
    category.sync_destination_attributes("ACCOUNT")

    new_account_count = DestinationAttribute.objects.filter(
        workspace_id=workspace_id, attribute_type="ACCOUNT"
    ).count()
    assert new_account_count == 2

    mocker.patch(
        "dynamics.apis.Locations.count",
        return_value=5
    )
    mocker.patch(
        "dynamics.apis.Locations.get_all",
        return_value=destination_attributes_data[
            "get_location_destination_attributes_0"
        ],
    )

    expense_type_count = DestinationAttribute.objects.filter(
        workspace_id=workspace_id, attribute_type="LOCATION"
    ).count()
    assert expense_type_count == 0

    category = Category(workspace_id, "LOCATION", None, [])
    category.sync_destination_attributes("LOCATION")

    new_expense_type_count = DestinationAttribute.objects.filter(
        workspace_id=workspace_id, attribute_type="LOCATION"
    ).count()
    assert new_expense_type_count == 2


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


def test_auto_create_destination_attributes(
    api_client,
    test_connection,
    create_temp_workspace,
    add_fyle_credentials,
    add_business_central_creds,
    mocker,
):
    category = Category(1, "ACCOUNT", None, [])
    category.sync_after = None

    Workspace.objects.filter(id=1).update(org_id="orwimNcVyYsp")
    # delete all destination attributes, expense attributes and mappings
    Mapping.objects.filter(
        workspace_id=1, source_type="CATEGORY", destination_type="ACCOUNT"
    ).delete()
    DestinationAttribute.objects.filter(
        workspace_id=1, attribute_type="ACCOUNT"
    ).delete()
    ExpenseAttribute.objects.filter(workspace_id=1, attribute_type="CATEGORY").delete()

    # create new case for account import
    with mock.patch("fyle.platform.apis.v1.admin.Categories.list_all") as mock_call:
        mocker.patch(
            "fyle_integrations_platform_connector.apis.Categories.post_bulk",
            return_value=[],
        )
        mocker.patch(
            "dynamics.apis.Accounts.count",
            return_value=5
        )
        mocker.patch(
            "dynamics.apis.Accounts.get_all",
            return_value=destination_attributes_data[
                "get_account_destination_attributes_1"
            ],
        )
        mock_call.side_effect = [
            destination_attributes_data[
                "create_new_auto_create_categories_expense_attributes_0"
            ],
            destination_attributes_data[
                "create_new_auto_create_categories_expense_attributes_1"
            ],
        ]

        expense_attributes_count = ExpenseAttribute.objects.filter(
            workspace_id=1, attribute_type="CATEGORY"
        ).count()

        assert expense_attributes_count == 0

        mappings_count = CategoryMapping.objects.filter(workspace_id=1).count()

        assert mappings_count == 0

        category.trigger_import()

        expense_attributes_count = ExpenseAttribute.objects.filter(
            workspace_id=1, attribute_type="CATEGORY"
        ).count()

        assert expense_attributes_count == 30

        mappings_count = CategoryMapping.objects.filter(workspace_id=1).count()

        assert mappings_count == 2


def test_construct_fyle_payload(
    api_client,
    test_connection,
    create_temp_workspace,
    add_fyle_credentials,
    add_business_central_creds,
    add_expense_destination_attributes_1,
    mocker,
):
    category = Category(1, "ACCOUNT", None, [])

    # create new case
    paginated_destination_attributes = DestinationAttribute.objects.filter(
        workspace_id=1, attribute_type="ACCOUNT"
    )
    existing_fyle_attributes_map = {}
    is_auto_sync_status_allowed = category.get_auto_sync_permission()

    fyle_payload = category.construct_fyle_payload(
        paginated_destination_attributes,
        existing_fyle_attributes_map,
        is_auto_sync_status_allowed,
    )

    assert (
        fyle_payload
        == destination_attributes_data["create_fyle_category_payload_create_new_case"]
    )

    # disable case
    DestinationAttribute.objects.filter(
        workspace_id=1, attribute_type="ACCOUNT", value__in=["Internet", "Meals"]
    ).update(active=False)

    ExpenseAttribute.objects.filter(
        workspace_id=1, attribute_type="ACCOUNT", value__in=["Internet", "Meals"]
    ).update(active=True)

    paginated_destination_attributes = DestinationAttribute.objects.filter(
        workspace_id=1, attribute_type="ACCOUNT"
    )

    paginated_destination_attribute_values = [
        attribute.value for attribute in paginated_destination_attributes
    ]
    existing_fyle_attributes_map = category.get_existing_fyle_attributes(
        paginated_destination_attribute_values
    )

    fyle_payload = category.construct_fyle_payload(
        paginated_destination_attributes,
        existing_fyle_attributes_map,
        is_auto_sync_status_allowed,
    )

    assert (
        fyle_payload
        == destination_attributes_data[
            "create_fyle_category_payload_create_disable_case"
        ]
    )
