from apps.workspaces.models import Workspace
from datetime import datetime
from fyle_accounting_mappings.models import DestinationAttribute, Mapping, CategoryMapping
from tests.test_business_central.fixtures import data


def test_post_attachments(
    db,
    mocker,
    create_business_central_connection

):
    business_central_connection = create_business_central_connection

    mocker.patch.object(
        business_central_connection.connection.attachments,
        'post',
        return_value={
            'id': 'Return_Attachment_Id',
            'name': 'Return_Attachment_Name',
        }
    )

    mocker.patch.object(
        business_central_connection.connection.attachments,
        'upload'
    )

    attachments = [
        {
            'id': 'Attachment_Id',
            'name': 'Attachment_Name',
            'content_type': 'image/png',
            'download_url': 'aHR0cHM6Ly9kb3dubG9hZHVybC5jb20='
        }
    ]

    ref_type = 'Expense'
    ref_id = 'Expense_Id'

    response = business_central_connection.post_attachments(
        ref_id=ref_id,
        ref_type=ref_type,
        attachments=attachments
    )

    assert len(response) == 2
    assert response['id'] == 'Return_Attachment_Id'
    assert response['name'] == 'Return_Attachment_Name'


def test_post_purchase_invoice(
    db,
    mocker,
    create_business_central_connection
):
    business_central_connection = create_business_central_connection

    mocker.patch.object(
        business_central_connection.connection.purchase_invoices,
        'post',
        return_value={
            'id': 'Return_Purchase_Invoice_Id',
        }
    )

    mocker.patch.object(
        business_central_connection.connection.purchase_invoice_line_items,
        'bulk_post',
        return_value=[
            {
                'id': 'Invoice_Line_Item_Id',
            },
            {
                'id': 'Invoice_Line_Item_Id_2',
            }
        ]
    )

    purchase_invoice_payload = {
        'id': 'Purchase_Invoice_Id',
        'name': 'Purchase_Invoice_Name',
    }

    purchase_invoice_lineitem_payload = [
        {
            'id': 'Purchase_Invoice_Line_Item_Id',
            'name': 'Purchase_Invoice_Line_Item_Name',
        },
        {
            'id': 'Purchase_Invoice_Line_Item_Id_2',
            'name': 'Purchase_Invoice_Line_Item_Name_2',
        }
    ]

    response = business_central_connection.post_purchase_invoice(
        purchase_invoice_payload=purchase_invoice_payload,
        purchase_invoice_lineitem_payload=purchase_invoice_lineitem_payload
    )

    assert len(response) == 2
    assert response['purchase_invoice_response']['id'] == 'Return_Purchase_Invoice_Id'
    assert response['bulk_post_response'][0]['id'] == 'Invoice_Line_Item_Id'
    assert response['bulk_post_response'][1]['id'] == 'Invoice_Line_Item_Id_2'


def test_bulk_post_journal_lineitems(
    db,
    mocker,
    create_business_central_connection,
    create_export_settings
):
    business_central_connection = create_business_central_connection

    mocker.patch.object(
        business_central_connection.connection.journal_line_items,
        'bulk_post',
        return_value=[
            {
                'id': 'Journal_Line_Item_Id',
            },
            {
                'id': 'Journal_Line_Item_Id_2',
            }
        ]
    )

    payload = [
        {
            'id': 'Journal_Line_Item_Id',
            'name': 'Journal_Line_Item_Name',
        },
        {
            'id': 'Journal_Line_Item_Id_2',
            'name': 'Journal_Line_Item_Name_2',
        }
    ]

    accounting_export = {
        'id': 'Accounting_Export_Id',
        'name': 'Accounting_Export_Name',
    }

    response = business_central_connection.bulk_post_journal_lineitems(
        payload=payload,
        accounting_export=accounting_export
    )

    assert len(response) == 2
    assert response[0]['id'] == 'Journal_Line_Item_Id'
    assert response[1]['id'] == 'Journal_Line_Item_Id_2'


def test_skip_sync_attributes(mocker, db, create_business_central_connection):

    today = datetime.today()
    Workspace.objects.filter(id=1).update(created_at=today)
    business_central_connection = create_business_central_connection

    Mapping.objects.filter(workspace_id=1).delete()
    CategoryMapping.objects.filter(workspace_id=1).delete()

    DestinationAttribute.objects.filter(workspace_id=1, attribute_type='VENDOR').delete()

    mocker.patch.object(
        business_central_connection.connection.vendors,
        'count',
        return_value=10001
    )

    business_central_connection.sync_vendors()

    vendors = DestinationAttribute.objects.filter(attribute_type='VENDOR', workspace_id=1).count()
    assert vendors == 0

    DestinationAttribute.objects.filter(workspace_id=1, attribute_type='LOCATION').delete()
    mocker.patch.object(
        business_central_connection.connection.locations,
        'count',
        return_value=1001
    )

    business_central_connection.sync_locations()

    locations = DestinationAttribute.objects.filter(attribute_type='LOCATION', workspace_id=1).count()
    assert locations == 0

    DestinationAttribute.objects.filter(workspace_id=1, attribute_type='ACCOUNT').delete()
    mocker.patch.object(
        business_central_connection.connection.accounts,
        'count',
        return_value=2001
    )

    business_central_connection.sync_accounts()

    accounts = DestinationAttribute.objects.filter(attribute_type='ACCOUNT', workspace_id=1).count()
    assert accounts == 0


def test_sync_bank_accounts(mocker, db, create_business_central_connection):
    workspace_id = 1
    business_central_connection = create_business_central_connection

    mocker.patch.object(
        business_central_connection.connection.bank_accounts,
        'get_all',
        return_value=data['bank_accounts']
    )

    mocker.patch.object(
        business_central_connection.connection.bank_accounts,
        'count',
        return_value=5
    )

    bank_account_count = DestinationAttribute.objects.filter(
        workspace_id=workspace_id, attribute_type="BANK_ACCOUNT"
    ).count()

    assert bank_account_count == 0
    business_central_connection.sync_bank_accounts()

    bank_accounts = DestinationAttribute.objects.filter(
        workspace_id=workspace_id, attribute_type="BANK_ACCOUNT"
    )

    assert bank_accounts.count() == 4


def test_sync_dimension(mocker, db, create_business_central_connection):

    workspace_id = 1
    business_central_connection = create_business_central_connection

    mocker.patch.object(
        business_central_connection.connection.dimensions,
        'get_all_dimensions',
        return_value=data['dimensions']
    )

    mocker.patch.object(
        business_central_connection.connection.dimensions,
        'count',
        return_value=5
    )

    mocker.patch.object(
        business_central_connection.connection.dimensions,
        'get_all_dimension_values',
        return_value=data['dimension_values']
    )

    mocker.patch.object(
        business_central_connection.connection.dimensions,
        'count_dimension_values',
        return_value=5
    )

    area_count = DestinationAttribute.objects.filter(
        workspace_id=workspace_id, attribute_type="AREA"
    ).count()

    assert area_count == 0
    business_central_connection.sync_dimensions()

    areas = DestinationAttribute.objects.filter(
        workspace_id=workspace_id, attribute_type="AREA"
    )
    assert areas.count() == 3
