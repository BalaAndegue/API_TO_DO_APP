from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    

    # API regroupée
    path('api/', include('Core.urls_api')),

    # Frontend classique
    path('', include('Core.urls_frontend')),
]
