from django.contrib import admin
from .models import *

admin.site.register(PasswordReset)
admin.site.register(User)
admin.site.register(Task)
admin.site.register(Category)
