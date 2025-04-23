from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError, NotFound


from Core.models import Task
from Core.serializers import TaskSerializer


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Task.objects.none() 

        user = self.request.user
        queryset = Task.objects.filter(user=user)

        priority = self.request.query_params.get('priority')
        category = self.request.query_params.get('category')
        if priority:
            queryset = queryset.filter(priority=priority)
        if category:
            queryset = queryset.filter(category=category)

        return queryset

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response({
            'success': True,
            'message': 'Liste des tâches récupérée avec succès',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(self.get_object())
            return Response({
                'success': True,
                'message': 'Tâche récupérée avec succès',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except NotFound:
            return Response({
                'success': False,
                'message': "Tâche introuvable"
            }, status=status.HTTP_404_NOT_FOUND)

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(user=request.user)
            self.perform_create(serializer)
            return Response({
                'success': True,
                'message': 'Tâche créée avec succès',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({
                'success': False,
                'message': 'Erreur de validation',
                'errors': e.detail
            }, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        task = self.get_object()
        if task.user != request.user:
            raise PermissionDenied("Vous ne pouvez modifier que vos propres tâches.")
        try:
            serializer = self.get_serializer(task, data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response({
                'success': True,
                'message': 'Tâche mise à jour avec succès, la liste des taches est : ',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({
                'success': False,
                'message': 'Erreur de validation',
                'errors': e.detail
            }, status=status.HTTP_400_BAD_REQUEST)


    def destroy(self, request, *args, **kwargs):
        if getattr(self, 'swagger_fake_view', False):
            return Response(status=status.HTTP_204_NO_CONTENT)

        try:
            task = Task.objects.filter(pk=kwargs.get("pk")).first()

            if not task:
                raise NotFound("Tâche introuvable.")

            if task.user != request.user:
                raise PermissionDenied("Vous ne pouvez supprimer que vos propres tâches.")

            self.perform_destroy(task)

            serializer = self.get_serializer(self.get_queryset(), many=True)

            return Response({
                'success': True,
                'message': 'Tâche supprimée avec succès',
                'data': serializer.data
            }, status=status.HTTP_200_OK)

        except PermissionDenied as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_403_FORBIDDEN)

        except NotFound as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({
                'success': False,
                'message': 'Une erreur est survenue',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
