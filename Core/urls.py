from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # API regroupée
    path('api/', include('Core.urls_api')),

    # Frontend classique
    path('', include('Core.urls_frontend')),
]
