"""
Workspace Serializers
"""
from django.core.cache import cache
from fyle_accounting_mappings.models import ExpenseAttribute
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


class ImportSettingsSerializer(serializers.ModelSerializer):
    """
    Import Settings serializer
    """
    class Meta:
        model = ImportSetting
        fields = '__all__'
        read_only_fields = ('id', 'workspace', 'created_at', 'updated_at')

    def create(self, validated_data):
        """
        Create Import Settings
        """

        workspace_id = self.context['request'].parser_context.get('kwargs').get('workspace_id')
        import_settings, _ = ImportSetting.objects.update_or_create(
            workspace_id=workspace_id,
            defaults=validated_data
        )

        # Update workspace onboarding state
        workspace = import_settings.workspace
        if workspace.onboarding_state == 'IMPORT_SETTINGS':
            workspace.onboarding_state = 'ADVANCED_SETTINGS'
            workspace.save()

        return import_settings


class AdvancedSettingSerializer(serializers.ModelSerializer):
    """
    Advanced Settings serializer
    """
    class Meta:
        model = AdvancedSetting
        fields = '__all__'
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
