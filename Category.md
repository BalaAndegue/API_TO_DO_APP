## 🏋️ Endpoints pour les Catégories dans la ToDo App

### 🌟 Objectif :
Permettre à un utilisateur authentifié de :

* 📥 Créer ses catégories de tâches.
****
* 📋 Lister les catégories de tâches

* ✏️ Modifier ses catégories de tâches.

* 🗑️ Supprimer ses catégories de tâches.
* 
---

### 📂 1. **Serializer** (`serializers.py`)

```python
from .models import Category
from rest_framework import serializers

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']
```

---

### 📅 2. **ViewSet** (`views.py`)

```python
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Category
from .serializers import CategorySerializer

class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
```

---

### 🌄 3. **Routing** (`urls.py`)

Dans le fichier `urls.py`, ajoute :

```python
from .views import CategoryViewSet

router.register(r'categories', CategoryViewSet, basename='category')
```

---

### 🌐 4. **Endpoints REST créés automatiquement**

| Méthode | URL                    | Action                       |
|----------|-------------------------|------------------------------|
| GET      | `/api/categories/`      | Lister les catégories        |
| POST     | `/api/categories/`      | Créer une catégorie         |
| GET      | `/api/categories/1/`    | Voir une catégorie           |
| PUT      | `/api/categories/1/`    | Modifier une catégorie       |
| DELETE   | `/api/categories/1/`    | Supprimer une catégorie      |

---

### ⚠️ Remarques :
- Seules les catégories de l'utilisateur connecté sont visibles/modifiables.
- Le champ `user` est automatiquement rempli dans `perform_create()`.
- À utiliser avec un système d'authentification comme JWT ou TokenAuth pour s'assurer que l'utilisateur est bien identifié.

---

****