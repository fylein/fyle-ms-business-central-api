from django.urls import path

from apps.workspaces.views import (
    ReadyView,
    WorkspaceView,
)


workspace_app_paths = [
    path('', WorkspaceView.as_view(), name='workspaces'),
    path('ready/', ReadyView.as_view(), name='ready'),

]

other_app_paths = []

urlpatterns = []
urlpatterns.extend(workspace_app_paths)
urlpatterns.extend(other_app_paths)
