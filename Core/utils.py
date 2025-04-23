from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.response import Response
from rest_framework import status

def custom_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    
    if response is not None:
        return Response({
            'success': False,
            'message': str(exc),
            'errors': response.data
        }, status=response.status_code)

    return response
