"""
Workspace Serializers
"""
from django.core.cache import cache
from django.db import transaction
from django.db.models import Q
from fyle_accounting_mappings.models import ExpenseAttribute, MappingSetting
from fyle_rest_auth.helpers import get_fyle_admin
from fyle_rest_auth.models import AuthToken
from rest_framework import serializers

from apps.accounting_exports.models import AccountingExportSummary
from apps.business_central.utils import BusinessCentralConnector
from apps.fyle.helpers import get_cluster_domain
from apps.users.models import User
from apps.workspaces.models import (
    AdvancedSetting,
    BusinessCentralCredentials,
    ExportSetting,
    FyleCredential,
    ImportSetting,
    Workspace,
)
from apps.workspaces.triggers import AdvancedSettingsTriggers, ImportSettingsTrigger
from ms_business_central_api.utils import assert_valid


class WorkspaceSerializer(serializers.ModelSerializer):
    """
    Workspace serializer
    """
    class Meta:
        model = Workspace
        fields = '__all__'
        read_only_fields = ('id', 'name', 'org_id', 'created_at', 'updated_at', 'user')

    def create(self, validated_data):
        """
        Update workspace
        """
        access_token = self.context['request'].META.get('HTTP_AUTHORIZATION')
        user = self.context['request'].user

        # Getting user profile using the access token
        fyle_user = get_fyle_admin(access_token.split(' ')[1], None)

        # getting name, org_id, currency of Fyle User
        name = fyle_user['data']['org']['name']
        org_id = fyle_user['data']['org']['id']

        # Checking if workspace already exists
        workspace = Workspace.objects.filter(org_id=org_id).first()

        if workspace:
            # Adding user relation to workspace
            workspace.user.add(User.objects.get(user_id=user))
            cache.delete(str(workspace.id))
        else:
            workspace = Workspace.objects.create(
                name=name,
                org_id=org_id,
            )

            workspace.user.add(User.objects.get(user_id=user))

            auth_tokens = AuthToken.objects.get(user__user_id=user)

            cluster_domain = get_cluster_domain(auth_tokens.refresh_token)

            AccountingExportSummary.objects.create(workspace_id=workspace.id)

            FyleCredential.objects.update_or_create(
                refresh_token=auth_tokens.refresh_token,
                workspace_id=workspace.id,
                cluster_domain=cluster_domain
            )

        if workspace.onboarding_state == 'CONNECTION':
            workspace.onboarding_state = 'COMPANY_SELECTION'
            workspace.save()

        return workspace


class BusinessCentralCredentialSerializer(serializers.ModelSerializer):
    """
    Business Central credential serializer
    """

    class Meta:
        model = BusinessCentralCredentials
        fields = "__all__"


class ExportSettingsSerializer(serializers.ModelSerializer):
    """
    Export Settings serializer
    """
    class Meta:
        model = ExportSetting
        fields = '__all__'
        read_only_fields = ('id', 'workspace', 'created_at', 'updated_at')

    def create(self, validated_data):
        """
        Create Export Settings
        """
        assert_valid(validated_data, 'Body cannot be null')

        if validated_data.get('reimbursable_expenses_export_type') == 'JOURNAL_ENTRY' or validated_data.get('credit_card_expense_export_type') == 'JOURNAL_ENTRY':
            assert_valid(validated_data.get('default_vendor_id'), 'Default Vendor cannot be null')

        if validated_data.get('reimbursable_expenses_export_type') == 'PURCHASE_INVOICE' and validated_data.get('credit_card_expense_export_type') == 'JOURNAL_ENTRY':
            assert_valid(validated_data.get('employee_field_mapping') == 'VENDOR', 'Employee mapping should be VENDOR')

        if validated_data.get('credit_card_expense_export_type') == 'JOURNAL_ENTRY' and validated_data.get('name_in_journal_entry') == 'MERCHANT':
            assert_valid(validated_data.get('default_vendor_id'), 'Default Vendor cannot be null')

        workspace_id = self.context['request'].parser_context.get('kwargs').get('workspace_id')

        export_settings, _ = ExportSetting.objects.update_or_create(
            workspace_id=workspace_id,
            defaults=validated_data
        )

        if (export_settings.reimbursable_expenses_export_type == 'JOURNAL_ENTRY' or export_settings.credit_card_expense_export_type == 'JOURNAL_ENTRY') and \
            not export_settings.journal_entry_folder_id:

            business_central_credentials = BusinessCentralCredentials.objects.get(workspace_id=workspace_id)
            business_central_connector = BusinessCentralConnector(business_central_credentials, workspace_id)

            journal_entry_folder_id = business_central_connector.create_journal_entry_folder()
            export_settings.journal_entry_folder_id = journal_entry_folder_id
            export_settings.save()

        # Update workspace onboarding state
        workspace = export_settings.workspace

        if workspace.onboarding_state == 'EXPORT_SETTINGS':
            workspace.onboarding_state = 'IMPORT_SETTINGS'
            workspace.save()

        return export_settings


class MappingSettingFilteredListSerializer(serializers.ListSerializer):
    """
    Serializer to filter the active system, which is a boolen field in
    System Model. The value argument to to_representation() method is
    the model instance
    """
    def to_representation(self, data):
        data = data.filter(~Q(
            destination_field__in=[
                'ACCOUNT',
                'EMPLOYEE',
                'VENDOR'
            ])
        )
        return super(MappingSettingFilteredListSerializer, self).to_representation(data)


class MappingSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = MappingSetting
        list_serializer_class = MappingSettingFilteredListSerializer
        fields = [
            'source_field',
            'destination_field',
            'import_to_fyle',
            'is_custom',
            'source_placeholder'
        ]


class ImportSettingFilterSerializer(serializers.ModelSerializer):
    """
    Import Settings Filtered serializer
    """
    class Meta:
        model = ImportSetting
        fields = [
            'import_categories',
            'import_vendors_as_merchants',
        ]


class ImportSettingsSerializer(serializers.ModelSerializer):
    """
    Import Settings serializer
    """
    import_settings = ImportSettingFilterSerializer()
    mapping_settings = MappingSettingSerializer(many=True)
    workspace_id = serializers.SerializerMethodField()

    class Meta:
        model = Workspace
        fields = [
            'import_settings',
            'mapping_settings',
            'workspace_id'
        ]
        read_only_fields = ['workspace_id']

    def get_workspace_id(self, instance):
        return instance.id

    def update(self, instance, validated):
        """
        Create Import Settings
        """

        mapping_settings = validated.pop('mapping_settings')
        import_settings = validated.pop('import_settings')

        with transaction.atomic():
            ImportSetting.objects.update_or_create(
                workspace_id=instance.id,
                defaults={
                    'import_categories': import_settings.get('import_categories'),
                    'import_vendors_as_merchants': import_settings.get('import_vendors_as_merchants')
                }
            )

            trigger: ImportSettingsTrigger = ImportSettingsTrigger(
                mapping_settings=mapping_settings,
                workspace_id=instance.id
            )

            for setting in mapping_settings:
                MappingSetting.objects.update_or_create(
                    destination_field=setting['destination_field'],
                    workspace_id=instance.id,
                    defaults={
                        'source_field': setting['source_field'],
                        'import_to_fyle': setting['import_to_fyle'] if 'import_to_fyle' in setting else False,
                        'is_custom': setting['is_custom'] if 'is_custom' in setting else False,
                        'source_placeholder': setting['source_placeholder'] if 'source_placeholder' in setting else None
                    }
                )

            trigger.post_save_mapping_settings()

        # Update workspace onboarding state
        if instance.onboarding_state == 'IMPORT_SETTINGS':
            instance.onboarding_state = 'ADVANCED_SETTINGS'
            instance.save()

        return instance

    def validate(self, data):
        if not data.get('import_settings'):
            raise serializers.ValidationError('Import Settings are required')

        if data.get('mapping_settings') is None:
            raise serializers.ValidationError('Mapping settings are required')

        return data


class AdvancedSettingSerializer(serializers.ModelSerializer):
    """
    Advanced Settings serializer
    """
    class Meta:
        model = AdvancedSetting
        fields = [
            'expense_memo_structure',
            'schedule_is_enabled',
            'interval_hours',
            'emails_selected',
            'emails_added',
            'auto_create_vendor'
        ]
        read_only_fields = ('id', 'workspace', 'created_at', 'updated_at')

    def create(self, validated_data):
        """
        Create Advanced Settings
        """
        workspace_id = self.context['request'].parser_context.get('kwargs').get('workspace_id')
        advanced_setting = AdvancedSetting.objects.filter(
            workspace_id=workspace_id).first()

        if not advanced_setting:
            if 'expense_memo_structure' not in validated_data:
                validated_data['expense_memo_structure'] = [
                    'employee_email',
                    'merchant',
                    'purpose',
                    'report_number'
                ]

        advanced_setting, _ = AdvancedSetting.objects.update_or_create(
            workspace_id=workspace_id,
            defaults=validated_data
        )

        # Update workspace onboarding state
        workspace = advanced_setting.workspace

        AdvancedSettingsTriggers.run_post_advance_settings_triggers(workspace_id, advanced_setting)
        if workspace.onboarding_state == 'ADVANCED_SETTINGS':
            workspace.onboarding_state = 'COMPLETE'
            workspace.save()

        return advanced_setting


class WorkspaceAdminSerializer(serializers.Serializer):
    """
    Workspace Admin Serializer
    """
    email = serializers.CharField()
    name = serializers.CharField()

    def get_admin_emails(self, workspace_id):
        """
        Get Workspace Admins
        """
        workspace = Workspace.objects.get(id=workspace_id)
        admin_emails = []

        users = workspace.user.all()

        for user in users:
            admin = User.objects.get(user_id=user)
            employee = ExpenseAttribute.objects.filter(value=admin.email, workspace_id=workspace_id, attribute_type='EMPLOYEE').first()
            if employee:
                admin_emails.append({'name': employee.detail['full_name'], 'email': admin.email})

        return admin_emails
