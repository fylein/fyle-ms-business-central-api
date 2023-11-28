from django.urls import path

from apps.business_central.views import ImportBusinessCentralAttributesView


urlpatterns = [
    path(
        "import_attributes/",
        ImportBusinessCentralAttributesView.as_view(),
        name="import-business-central-attributes",
    )
]
