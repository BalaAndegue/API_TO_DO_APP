"""
URL configuration for AuthenticationProject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from rest_framework.authentication import TokenAuthentication

api_info = openapi.Info(
    title="Collaborative Workspace API",
    default_version='v1',
    description=(
        "REST API for a Trello-like collaborative workspace.\n\n"
        "**Authentication** — All endpoints (except `/register/` and `/login/`) require a token:\n"
        "```\nAuthorization: Token <your_token>\n```\n\n"
        "**Key resources:** Boards → Lists → Cards → Checklists / Labels / Comments / Attachments\n\n"
        "**Roles:** Each board has members with roles `admin`, `member`, or `observer`."
    ),
    terms_of_service="https://www.example.com/terms/",
    contact=openapi.Contact(email="contact@example.com"),
    license=openapi.License(name="MIT License"),
)

schema_view = get_schema_view(
    api_info,
    public=True,
    permission_classes=(permissions.AllowAny,),
    authentication_classes=(TokenAuthentication,),  
)

urlpatterns = [
     path('admin/', admin.site.urls),
    path('', include('Core.urls')), # Restored correct include
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('openapi.json', schema_view.without_ui(cache_timeout=0), name='openapi-json'),
]
