from django.contrib import admin
from .models import PasswordReset, User

admin.site.register(PasswordReset)

admin.site.register(User)