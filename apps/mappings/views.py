from django_q.tasks import Chain
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import status


class AutoMapEmployeeView(generics.CreateAPIView):
    """
    Auto Map Employee view
    """

    def post(self, request, *args, **kwargs):
        """
        Trigger Auto Map Employees
        """
        workspace_id = kwargs['workspace_id']

        chain = Chain()

        chain.append('apps.mappings.tasks.async_auto_map_employees', workspace_id)

        chain.run()

        return Response(
            data={},
            status=status.HTTP_200_OK
        )
