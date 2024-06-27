# Generated by Django 5.0.6 on 2024-06-27 09:33

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="Category",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("name", models.CharField(max_length=100, verbose_name="Category name")),
            ],
            options={
                "verbose_name": "Category",
                "verbose_name_plural": "List of categories",
                "ordering": ("-name",),
            },
        ),
        migrations.CreateModel(
            name="Parameter",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("name", models.CharField(max_length=100, verbose_name="Parameter name")),
            ],
            options={
                "verbose_name": "Parameter",
                "verbose_name_plural": "List of parameters",
                "ordering": ("-name",),
            },
        ),
        migrations.CreateModel(
            name="Shop",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("name", models.CharField(max_length=100, verbose_name="Shop name")),
                ("url", models.URLField(blank=True, null=True, verbose_name="Shop URL")),
            ],
            options={
                "verbose_name": "Shop",
                "verbose_name_plural": "List of shops",
                "ordering": ("-name",),
            },
        ),
        migrations.CreateModel(
            name="User",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                (
                    "last_login",
                    models.DateTimeField(blank=True, null=True, verbose_name="last login"),
                ),
                (
                    "is_superuser",
                    models.BooleanField(
                        default=False,
                        help_text="Designates that this user has "
                        "all permissions without explicitly assigning them.",
                        verbose_name="superuser status",
                    ),
                ),
                (
                    "type",
                    models.CharField(
                        choices=[("shop", "Shop"), ("buyer", "Buyer")],
                        default="buyer",
                        max_length=20,
                        verbose_name="Type",
                    ),
                ),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("first_name", models.CharField(max_length=30)),
                ("last_name", models.CharField(max_length=30)),
                ("middle_name", models.CharField(blank=True, max_length=30)),
                ("company", models.CharField(blank=True, max_length=100)),
                ("position", models.CharField(blank=True, max_length=100)),
                ("is_active", models.BooleanField(default=True)),
                ("is_staff", models.BooleanField(default=False)),
                ("date_joined", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        related_name="custom_user_groups",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        related_name="custom_user_permissions",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={
                "verbose_name": "User",
                "verbose_name_plural": "Users",
            },
        ),
        migrations.CreateModel(
            name="Contact",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "phone",
                    models.CharField(
                        max_length=20,
                        unique=True,
                        validators=[
                            django.core.validators.RegexValidator(
                                message="Phone number must be entered in the "
                                "format: '+999999999'. Up to 15 digits allowed.",
                                regex="^\\+?1?\\d{9,15}$",
                            )
                        ],
                        verbose_name="Phone",
                    ),
                ),
                ("city", models.CharField(blank=True, max_length=100, verbose_name="City")),
                ("street", models.CharField(blank=True, max_length=100, verbose_name="Street")),
                ("house", models.CharField(blank=True, max_length=100, verbose_name="House")),
                (
                    "structure",
                    models.CharField(blank=True, max_length=100, verbose_name="Structure"),
                ),
                ("building", models.CharField(blank=True, max_length=100, verbose_name="Building")),
                (
                    "apartment",
                    models.CharField(blank=True, max_length=100, verbose_name="Apartment"),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="contacts",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="User",
                    ),
                ),
            ],
            options={
                "verbose_name": "Contact",
                "verbose_name_plural": "List of contacts",
            },
        ),
        migrations.CreateModel(
            name="Order",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("date", models.DateField(auto_now_add=True, verbose_name="Date")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("new", "New"),
                            ("confirmed", "Confirmed"),
                            ("assembled", "Assembled"),
                            ("sent", "Sent"),
                            ("delivered", "Delivered"),
                            ("canceled", "Canceled"),
                            ("returned", "Returned"),
                        ],
                        default="new",
                        max_length=20,
                        verbose_name="Status",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="orders",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="User",
                    ),
                ),
            ],
            options={
                "verbose_name": "Order",
                "verbose_name_plural": "List of orders",
                "ordering": ("-date",),
            },
        ),
        migrations.CreateModel(
            name="Product",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("name", models.CharField(max_length=100, verbose_name="Product name")),
                (
                    "category",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="products",
                        to="backend.category",
                    ),
                ),
            ],
            options={
                "verbose_name": "Product",
                "verbose_name_plural": "List of products",
                "ordering": ("-name",),
            },
        ),
        migrations.CreateModel(
            name="ProductInfo",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("quantity", models.PositiveIntegerField(verbose_name="Quantity")),
                ("price", models.PositiveIntegerField(verbose_name="Price")),
                (
                    "price_rrc",
                    models.PositiveIntegerField(
                        blank=True, null=True, verbose_name="Recommended retail price"
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="product_infos",
                        to="backend.product",
                        verbose_name="Product",
                    ),
                ),
                (
                    "shop",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="shop_infos",
                        to="backend.shop",
                        verbose_name="Shop",
                    ),
                ),
            ],
            options={
                "verbose_name": "Product information",
                "verbose_name_plural": "List of products information",
            },
        ),
        migrations.CreateModel(
            name="ProductParameter",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("value", models.CharField(max_length=100, verbose_name="Parameter value")),
                (
                    "parameter",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="product_parameters",
                        to="backend.parameter",
                        verbose_name="Parameter",
                    ),
                ),
                (
                    "product_info",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="parameters",
                        to="backend.productinfo",
                        verbose_name="Product information",
                    ),
                ),
            ],
            options={
                "verbose_name": "Product parameter",
                "verbose_name_plural": "List of product parameters",
            },
        ),
        migrations.CreateModel(
            name="OrderItem",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("quantity", models.PositiveIntegerField(verbose_name="Quantity")),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="order_items",
                        to="backend.order",
                        verbose_name="Order",
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="order_items",
                        to="backend.product",
                        verbose_name="Product",
                    ),
                ),
                (
                    "shop",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="shop_items",
                        to="backend.shop",
                        verbose_name="Shop",
                    ),
                ),
            ],
            options={
                "verbose_name": "Ordered item",
                "verbose_name_plural": "List of ordered items",
            },
        ),
        migrations.AddField(
            model_name="category",
            name="shops",
            field=models.ManyToManyField(
                related_name="categories", to="backend.shop", verbose_name="Shops"
            ),
        ),
    ]
