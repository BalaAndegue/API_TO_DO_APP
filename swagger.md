## 📃 Documentation API avec Swagger (drf-yasg)

### 🔧 Objectif
Mettre en place une documentation interactive de l'API avec Swagger UI dans Django REST Framework.

---

## 👍 INTRO 
Swagger (ou plus précisément drf-yasg dans Django) sert à générer automatiquement une documentation interactive de l' API REST. Voici pourquoi c’est super utile, surtout dans notre app ToDo App :

## 🔍 À quoi sert Swagger ?
:arrow_right:1. Documenter l' API

    Chaque endpoint est listé automatiquement avec :

* :arrow_forward: son URL,

* :arrow_forward: la méthode (GET, POST, etc.),

* :arrow_forward:  les champs attendus (inputs),

* :arrow_forward: la réponse (outputs),

* :arrow_forward: les codes d'erreur possibles.

:arrow_right: 2. Tester ton API directement dans le navigateur

    On peut  envoyer des requêtes directement depuis l'interface Swagger, comme un mini Postman dans le  navigateur.

:arrow_right: 3. Gagner du temps en équipe

    Si l'on travaille avec un développeur frontend, il saura tout de suite comment utiliser l' API sans que l'on lui  écrive de doc manuellement.

:arrow_right: 4. Maintenir la  doc sera  à jour automatiquement

    Chaque fois que l'on ajoutes ou modifies un endpoint dans le  code, Swagger le met à jour automatiquement.


# 📘 Swagger Integration dans Django

## 🧩 Installation des dépendances
```bash
pip install drf-yasg
```

## ⚙️ Configuration du Swagger dans `urls.py`
```python
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

schema_view = get_schema_view(
   openapi.Info(
      title="API TO DO",
      default_version='v1',
      description="Documentation de l'API TO DO App",
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    ...
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
]
```

## 📁 Template personnalisé si besoin (optionnel)
Créer le fichier `templates/drf-yasg/swagger-ui.html` si erreur de template manquant :

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8">
    <title>Swagger UI</title>
    <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist/swagger-ui.css" />
  </head>
  <body>
    <div id="swagger-ui"></div>
    <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist/swagger-ui-bundle.js"></script>
    <script>
      const ui = SwaggerUIBundle({
        url: "{% url 'schema-json' %}",
        dom_id: '#swagger-ui',
      });
    </script>
  </body>
</html>
```

## 🏁 Lancer le serveur
```bash
python manage.py runserver
```

Puis accède à :
- Swagger UI : [http://localhost:8000/swagger/](http://localhost:8000/swagger/)
- ReDoc UI : [http://localhost:8000/redoc/](http://localhost:8000/redoc/)

---

### ✅ Avantages
- Affiche tous les endpoints disponibles
- Permet de faire des requêtes directement via l'interface
- Affiche les champs des modèles depuis les serializers
- Gère les permissions (authentification requise, etc.)

---

### 📄 Recommandation
Inclure `drf-yasg` seulement en mode développement pour éviter de l'exposer en production (via `if settings.DEBUG:` dans `urls.py`).

