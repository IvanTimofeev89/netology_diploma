from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    Category,
    Contact,
    Order,
    OrderItem,
    Product,
    ProductInfo,
    ProductParameter,
    Shop,
    User,
)


class UserContactInline(admin.TabularInline):
    model = Contact
    extra = 0
    fields = ("city", "street", "house", "structure", "building", "apartment", "phone")
    readonly_fields = ("city", "street", "house", "structure", "building", "apartment", "phone")


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    fieldsets = (
        (None, {"fields": ("email", "password", "type")}),
        ("Personal info", {"fields": ("first_name", "last_name", "company", "position")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_email_confirmed",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    list_display = ("email", "first_name", "last_name", "is_staff", "type")
    list_filter = ("is_staff", "is_superuser", "is_email_confirmed")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)
    filter_horizontal = ()
    inlines = [UserContactInline]


# class ProductParameterInline(NonrelatedTabularInline):
#     model = ProductParameter
#     extra = 0
#     fields = ('parameter', 'value')
#     readonly_fields = ('parameter', 'value')
#
#     def get_form_queryset(self, obj):
#         return ProductParameter.objects.filter(product=obj)
#
#     def save_new_instance(self, parent, instance):
#         instance.product_info = parent
#         super().save_new_instance(parent, instance)

# parameter.short_description = 'Parameter'


class ProductInfoInline(admin.TabularInline):
    model = ProductInfo
    extra = 0
    readonly_fields = ("product", "shop", "quantity", "price", "price_rrc", "external_id")


class ProductParametersInline(admin.TabularInline):
    model = ProductParameter
    extra = 0
    fields = ("parameter", "value")
    readonly_fields = ("parameter", "value")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    model = Product
    list_display = ("name", "category")
    readonly_fields = ("name", "category")
    list_filter = ("category",)
    search_fields = ("name", "category")

    inlines = [ProductInfoInline, ProductParametersInline]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    model = Category
    list_display = ("name", "external_id")
    readonly_fields = ("name", "external_id")
    list_filter = ("name", "external_id")
    search_fields = ("name", "external_id")


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    model = Shop
    list_display = ("name", "url", "state")


class OrderItemInline(admin.StackedInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "shop")
    fields = ("product", "shop", "quantity")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("user", "status", "date")
    list_filter = (
        "user",
        "status",
    )
    search_fields = ("user", "status")

    fieldsets = (
        (None, {"fields": ("user", "status", "date")}),
        (
            "Order Details",
            {
                "fields": ("total",),
            },
        ),
    )

    readonly_fields = ("total", "date", "user")

    inlines = [OrderItemInline]

    def total(self, obj):
        total_amount = sum(
            item.product_info.price_rrc * item.quantity for item in obj.order_items.all()
        )
        return total_amount

    total.short_description = "Total"
