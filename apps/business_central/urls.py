from django.urls import path

from apps.business_central.views import BusinessCentralFieldsView, ImportBusinessCentralAttributesView

urlpatterns = [
    path(
        "import_attributes/",
        ImportBusinessCentralAttributesView.as_view(),
        name="import-business-central-attributes",
    ),
    path("fields/", BusinessCentralFieldsView.as_view(), name="business-central-fields"),
]
