from django.urls import include, path

from apps.workspaces.views import (
    AdvancedSettingView,
    ConnectBusinessCentralView,
    ExportSettingView,
    ImportSettingView,
    ReadyView,
    TriggerExportsView,
    WorkspaceAdminsView,
    WorkspaceView,
)

workspace_app_paths = [
    path('', WorkspaceView.as_view(), name='workspaces'),
    path('ready/', ReadyView.as_view(), name='ready'),
    path('<int:workspace_id>/exports/trigger/', TriggerExportsView.as_view(), name='trigger-exports'),
    path("<int:workspace_id>/connect_business_central/authorization_code/", ConnectBusinessCentralView.as_view(), name='business-central-authorization-code'),
    path("<int:workspace_id>/credentials/business_central/", ConnectBusinessCentralView.as_view(), name='business-central-credentials'),
    path('<int:workspace_id>/export_settings/', ExportSettingView.as_view(), name='export-settings'),
    path('<int:workspace_id>/import_settings/', ImportSettingView.as_view(), name='import-settings'),
    path('<int:workspace_id>/advanced_settings/', AdvancedSettingView.as_view(), name='advanced-settings'),
    path('<int:workspace_id>/admins/', WorkspaceAdminsView.as_view(), name='admin'),
]

other_app_paths = [
    path('<int:workspace_id>/accounting_exports/', include('apps.accounting_exports.urls')),
    path('<int:workspace_id>/fyle/', include('apps.fyle.urls')),
    path('<int:workspace_id>/business_central/', include('apps.business_central.urls')),
    path('<int:workspace_id>/mappings/', include('apps.mappings.urls'))
]

urlpatterns = []
urlpatterns.extend(workspace_app_paths)
urlpatterns.extend(other_app_paths)
