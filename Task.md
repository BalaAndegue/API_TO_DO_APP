# 🎯 Objectif aujourd'hui :

Créer les endpoints pour les tâches (Task) : utilisant Kanban

* 📥 Créer une tâche

* 📋 Lister les tâches de l’utilisateur connecté

* 🔎 Voir une tâche

* ✏️ Modifier une tâche

* 🗑️ Supprimer une tâche
* 
## 🌟 Endpoints pour les Tâches (Task)

Ce fichier documente les étapes de mise en place des endpoints pour le modèle `Task` dans l'application ToDo App avec Django REST Framework.

---

## 🏛️ Modèle concerné : `Task`

- Titre
- Description
- Statut (terminé ou non)
- Date de début / fin
- Rappel
- Priorité

---

## ✨ Etape 1 : Serializer

Fichier : `serializers.py`

```python
from rest_framework import serializers
from .models import Task

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']
```

---

## 🧐 Etape 2 : ViewSet

Fichier : `views.py`

```python
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Task
from .serializers import TaskSerializer

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
```

---

## 🚧 Etape 3 : URL Routing

Fichier : `urls.py`

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TaskViewSet

router = DefaultRouter()
router.register(r'tasks', TaskViewSet, basename='task')

urlpatterns = [
    path('api/', include(router.urls)),
]
```

---

## 🚀 Endpoints disponibles

| Méthode | URL              | Action                       |
|----------|------------------|------------------------------|
| GET      | `/api/tasks/`     | Lister les tâches de l'utilisateur |
| POST     | `/api/tasks/`     | Créer une nouvelle tâche       |
| GET      | `/api/tasks/{id}/` | Détail d'une tâche            |
| PUT/PATCH| `/api/tasks/{id}/` | Modifier une tâche            |
| DELETE   | `/api/tasks/{id}/` | Supprimer une tâche           |

---

## 🔒 Permissions et Authentification

Dans `settings.py` :

```python
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
}
```

L'utilisateur doit être connecté pour accéder aux endpoints et effectuer des operations diverses.

---

Prêt à créer les endpoints pour `Category` ou mettre en place l'inscription/login ?

****
