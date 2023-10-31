from django.urls import path

from apps.workspaces.views import (
    ReadyView,
    WorkspaceView,
    ExportSettingView,
    ImportSettingView
)


workspace_app_paths = [
    path('', WorkspaceView.as_view(), name='workspaces'),
    path('ready/', ReadyView.as_view(), name='ready'),
    path('<int:workspace_id>/export_settings/', ExportSettingView.as_view(), name='export-settings'),
    path('<int:workspace_id>/import_settings/', ImportSettingView.as_view(), name='import-settings'),

]

other_app_paths = []

urlpatterns = []
urlpatterns.extend(workspace_app_paths)
urlpatterns.extend(other_app_paths)
