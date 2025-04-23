from rest_framework.views import exception_handler
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated, PermissionDenied
from rest_framework.response import Response
from rest_framework import status

def custom_exception_handler(exc, context):
    # Appelle la gestion d'exception par défaut d'abord
    response = exception_handler(exc, context)
  
        
    if isinstance(exc, NotAuthenticated):
        return Response({
            'success': False,
            'message': 'Authentification requise pour accéder à cette ressource.',
        }, status=status.HTTP_401_UNAUTHORIZED)

    elif isinstance(exc, AuthenticationFailed):
        return Response({
            'success': False,
            'message': 'Identifiants invalides. Veuillez vérifier votre email et mot de passe.',
        }, status=status.HTTP_401_UNAUTHORIZED)

    elif isinstance(exc, PermissionDenied):
        return Response({
            'success': False,
            'message': 'Vous n\'avez pas la permission d\'effectuer cette action.',
        }, status=status.HTTP_403_FORBIDDEN)

    # Optionnel : toutes les autres exceptions avec structure personnalisée
    elif response is not None:
        return Response({
            'success': False,
            'message': response.data.get('detail', 'Une erreur est survenue.'),
        }, status=response.status_code)

    return response

   


