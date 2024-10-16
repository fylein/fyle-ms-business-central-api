from unittest import mock

from fyle_accounting_mappings.models import DestinationAttribute, ExpenseAttribute, Mapping
from fyle_integrations_platform_connector import PlatformConnector

from apps.mappings.imports.modules.merchants import Merchant
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
    platform = PlatformConnector(fyle_credentials=fyle_credentials)
    ExpenseAttribute.objects.filter(
        workspace_id=workspace_id, attribute_type="MERCHANT"
    ).delete()

    merchants_count = ExpenseAttribute.objects.filter(
        workspace_id=workspace_id, attribute_type="MERCHANT"
    ).count()
    assert merchants_count == 0

    mocker.patch(
        "fyle.platform.apis.v1beta.admin.ExpenseFields.list_all", return_value=[]
    )

    merchant = Merchant(workspace_id, "VENDOR", None)
    merchant.sync_expense_attributes(platform)

    merchants_count = ExpenseAttribute.objects.filter(
        workspace_id=workspace_id, attribute_type="MERCHANT"
    ).count()
    assert merchants_count == 0

    mocker.patch(
        "fyle.platform.apis.v1beta.admin.ExpenseFields.list_all",
        return_value=data["create_new_auto_create_merchants_expense_attributes_0"],
    )

    merchant.sync_expense_attributes(platform)

    merchants_count = ExpenseAttribute.objects.filter(
        workspace_id=workspace_id, attribute_type="MERCHANT"
    ).count()
    assert merchants_count == 72


def test_sync_destination_atrributes(
    api_client,
    test_connection,
    create_temp_workspace,
    add_fyle_credentials,
    add_business_central_creds,
    mocker,
):
    mocker.patch(
        "dynamics.apis.Vendors.count",
        return_value=5,
    )
    mocker.patch(
        "dynamics.apis.Vendors.get_all",
        return_value=data["get_vendors_destination_attributes"],
    )
    workspace_id = 1

    vendors_count = DestinationAttribute.objects.filter(
        workspace_id=workspace_id, attribute_type="VENDOR"
    ).count()
    assert vendors_count == 0

    tax_group = Merchant(workspace_id, "VENDOR", None)
    tax_group.sync_destination_attributes("VENDOR")

    vendors_count = DestinationAttribute.objects.filter(
        workspace_id=workspace_id, attribute_type="VENDOR"
    ).count()
    assert vendors_count == 2


def test_auto_create_destination_attributes(
    api_client,
    test_connection,
    create_temp_workspace,
    add_fyle_credentials,
    add_business_central_creds,
    mocker,
):
    workspace_id = 1
    merchant = Merchant(workspace_id, "VENDOR", None)
    merchant.sync_after = None

    # delete all destination attributes, expense attributes and mappings
    Mapping.objects.filter(
        workspace_id=1, source_type="MERCHANT", destination_type="VENDOR"
    ).delete()
    # DestinationAttribute.objects.filter(workspace_id=1, attribute_type='VENDOR').delete()
    ExpenseAttribute.objects.filter(workspace_id=1, attribute_type="MERCHANT").delete()

    # create new case for tax-groups import
    with mock.patch(
        "fyle.platform.apis.v1beta.admin.ExpenseFields.list_all"
    ) as mock_call:
        mocker.patch(
            "fyle_integrations_platform_connector.apis.Merchants.post", return_value=[]
        )
        mocker.patch(
            "dynamics.apis.Vendors.count",
            return_value=5,
        )
        mocker.patch(
            "dynamics.apis.Vendors.get_all",
            return_value=data["get_vendors_destination_attributes"],
        )

        mock_call.side_effect = [
            data["create_new_auto_create_merchants_expense_attributes_0"],
            data["create_new_auto_create_merchants_expense_attributes_1"],
        ]

        expense_attributes_count = ExpenseAttribute.objects.filter(
            workspace_id=1, attribute_type="MERCHANT"
        ).count()

        assert expense_attributes_count == 0

        mappings_count = Mapping.objects.filter(
            workspace_id=1, source_type="MERCHANT", destination_type="VENDOR"
        ).count()

        assert mappings_count == 0

        merchant.trigger_import()

        expense_attributes_count = ExpenseAttribute.objects.filter(
            workspace_id=1, attribute_type="MERCHANT"
        ).count()

        assert expense_attributes_count == 73

        # We dont create any mapping for VENDOR and MERCHANT, so this should be 0
        mappings_count = Mapping.objects.filter(
            workspace_id=1, source_type="MERCHANT", destination_type="VENDOR"
        ).count()

        assert mappings_count == 0

    # create new tax-groups sub-sequent run (we will be adding 2 new tax-details)
    with mock.patch(
        "fyle.platform.apis.v1beta.admin.ExpenseFields.list_all"
    ) as mock_call:
        mocker.patch(
            "fyle_integrations_platform_connector.apis.Merchants.post", return_value=[]
        )
        mocker.patch(
            "dynamics.apis.Vendors.count",
            return_value=5,
        )
        mocker.patch(
            "dynamics.apis.Vendors.get_all",
            return_value=data["get_vendors_destination_attributes_subsequent_run"],
        )

        mock_call.side_effect = [
            data["create_new_auto_create_merchants_expense_attributes_1"],
            data["create_new_auto_create_merchants_expense_attributes_2"],
        ]

        expense_attributes_count = ExpenseAttribute.objects.filter(
            workspace_id=1, attribute_type="MERCHANT"
        ).count()

        assert expense_attributes_count == 73

        mappings_count = Mapping.objects.filter(
            workspace_id=1, source_type="MERCHANT", destination_type="VENDOR"
        ).count()

        assert mappings_count == 0

        merchant.trigger_import()

        expense_attributes_count = ExpenseAttribute.objects.filter(
            workspace_id=1, attribute_type="MERCHANT"
        ).count()

        assert expense_attributes_count == 73 + 2

        # We dont create any mapping for VENDOR and MERCHANT, so this should be 0
        mappings_count = Mapping.objects.filter(
            workspace_id=1, source_type="MERCHANT", destination_type="VENDOR"
        ).count()

        assert mappings_count == 0


def test_construct_fyle_payload(
    api_client,
    test_connection,
    mocker,
    create_temp_workspace,
    add_business_central_creds,
    add_fyle_credentials,
    add_merchant_mappings,
):
    merchant = Merchant(1, "MERCHANT", None)

    # create new case
    paginated_destination_attributes = DestinationAttribute.objects.filter(
        workspace_id=1, attribute_type="MERCHANT"
    )

    existing_fyle_attributes_map = {}
    is_auto_sync_status_allowed = merchant.get_auto_sync_permission()

    fyle_payload = merchant.construct_fyle_payload(
        paginated_destination_attributes,
        existing_fyle_attributes_map,
        is_auto_sync_status_allowed,
    )

    assert fyle_payload == ["Direct Mail Campaign", "Platform APIs"]
