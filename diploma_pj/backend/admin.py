from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Shop, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    fieldsets = (
        (None, {"fields": ("email", "password", "type")}),
        ("Personal info", {"fields": ("first_name", "last_name", "company", "position")}),
        (
            "Permissions",
            {
                "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    list_display = ("email", "first_name", "last_name", "is_staff", "type")
    list_filter = ("is_staff", "is_superuser", "is_active")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)
    filter_horizontal = ()


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    model = Shop
    list_display = ("name", "url")
