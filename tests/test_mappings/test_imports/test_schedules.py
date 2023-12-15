from django_q.models import Schedule
from fyle_accounting_mappings.models import MappingSetting

from apps.mappings.imports.schedules import schedule_or_delete_fyle_import_tasks
from apps.workspaces.models import ImportSetting


def test_schedule_projects_creation(api_client, test_connection, create_temp_workspace, add_fyle_credentials, add_import_settings, add_mapping_settings):
    workspace_id = 1

    # Test schedule projects creation
    import_setting = ImportSetting.objects.get(workspace_id=workspace_id)
    import_setting.import_categories = True
    import_setting.import_vendors_as_merchants = True
    import_setting.save()

    mapping_setting = MappingSetting.objects.filter(workspace_id=workspace_id, source_field='CATEGORY', destination_field='ACCOUNT', import_to_fyle=True).first()

    schedule_or_delete_fyle_import_tasks(import_setting, mapping_setting)

    schedule = Schedule.objects.filter(
        func='apps.mappings.imports.queues.chain_import_fields_to_fyle',
        args='{}'.format(workspace_id),
    ).first()

    assert schedule.func == 'apps.mappings.imports.queues.chain_import_fields_to_fyle'

    # Test delete schedule projects creation
    import_setting = ImportSetting.objects.get(workspace_id=workspace_id)
    import_setting.import_categories = False
    import_setting.import_vendors_as_merchants = False
    import_setting.save()

    mapping_setting = MappingSetting.objects.filter(workspace_id=workspace_id, source_field='CATEGORY', destination_field='ACCOUNT', import_to_fyle=True).first()
    mapping_setting.import_to_fyle = False
    mapping_setting.save()

    schedule_or_delete_fyle_import_tasks(import_setting, mapping_setting)

    schedule = Schedule.objects.filter(
        func='apps.mappings.imports.queues.chain_import_fields_to_fyle',
        args='{}'.format(workspace_id),
    ).first()

    assert schedule == None

    # Test schedule categories creation adding the new schedule and not adding the old one
    import_setting = ImportSetting.objects.get(workspace_id=workspace_id)
    import_setting.import_categories = True
    import_setting.import_vendors_as_merchants = False
    import_setting.save()

    schedule_or_delete_fyle_import_tasks(import_setting, mapping_setting)

    schedule = Schedule.objects.filter(
        func='apps.mappings.imports.queues.chain_import_fields_to_fyle',
        args='{}'.format(workspace_id),
    ).first()

    assert schedule.func == 'apps.mappings.imports.queues.chain_import_fields_to_fyle'
