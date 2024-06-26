from django.contrib import admin

from .models import User


class CustomUserAdmin(admin.ModelAdmin):
    list_display = (
        "first_name",
        "last_name",
        "email",
    )


admin.site.register(User, CustomUserAdmin)
