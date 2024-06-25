from django.db import models
from django.contrib.auth.models import User

STATUS_CHOICES = (
    ("new", "New"),
    ("confirmed", "Confirmed"),
    ("assembled", "Assembled"),
    ("sent", "Sent"),
    ("delivered", "Delivered"),
    ("canceled", "Canceled"),
    ("returned", "Returned"),
)

CONTACT_TYPES = (
    ("shop", "Shop"),
    ("buyer", "Buyer"),
)


class Shop(models.Model):
    name = models.CharField(max_length=100, verbose_name="Shop name")
    url = models.URLField(null=True, blank=True, verbose_name="Shop URL")

    class Meta:
        verbose_name = "Shop"
        verbose_name_plural = "List of shops"
        ordering = ("-name",)


class Category(models.Model):
    shops = models.ManyToManyField(
        Shop, verbose_name="Shops", related_name="categories"
    )
    name = models.CharField(max_length=100, verbose_name="Category name")

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "List of categories"
        ordering = ("-name",)


class Product(models.Model):
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="products"
    )
    name = models.CharField(max_length=100, verbose_name="Product name")

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "List of products"
        ordering = ("-name",)


class ProductInfo(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, verbose_name="Product"
    )
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, verbose_name="Shop")
    name = models.CharField(max_length=100, verbose_name="Product name")
    quantity = models.PositiveIntegerField(verbose_name="Quantity")
    price = models.PositiveIntegerField(verbose_name="Price")
    price_rrc = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Recommended retail price"
    )

    class Meta:
        verbose_name = "Product information"
        verbose_name_plural = "List of products information"
        ordering = ("-name",)


class Parameter(models.Model):
    name = models.CharField(max_length=100, verbose_name="Parameter name")

    class Meta:
        verbose_name = "Parameter"
        verbose_name_plural = "List of parameters"
        ordering = ("-name",)


class ProductParameter(models.Model):
    product_info = models.ForeignKey(
        ProductInfo,
        on_delete=models.CASCADE,
        verbose_name="Product information",
        related_name="parameters",
    )
    parameter = models.ForeignKey(
        Parameter,
        on_delete=models.CASCADE,
        verbose_name="Parameter",
        related_name="product_parameters",
    )
    value = models.CharField(max_length=100, verbose_name="Parameter value")

    class Meta:
        verbose_name = "Product parameter"
        verbose_name_plural = "List of product parameters"


class Order(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="User", related_name="orders"
    )
    date = models.DateField(verbose_name="Date", auto_now_add=True)
    status = models.CharField(
        choises=STATUS_CHOICES, default="new", verbose_name="Status", max_length=20
    )

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "List of orders"
        ordering = ("-date",)


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        verbose_name="Order",
        related_name="order_items",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        verbose_name="Product",
        related_name="order_items",
    )
    shop = models.ForeignKey(
        Shop, on_delete=models.CASCADE, verbose_name="Shop", related_name="shop_items"
    )
    quantity = models.PositiveIntegerField(verbose_name="Quantity")

    class Meta:
        verbose_name = "Ordered item"
        verbose_name_plural = "List of ordered items"


class Contact(models.Model):
    type = models.CharField(choices=CONTACT_TYPES, verbose_name="Type", max_length=20)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="User", related_name="contacts"
    )
    name = models.CharField(max_length=100, verbose_name="Name")
    phone = models.CharField(max_length=20, verbose_name="Phone")

    class Meta:
        verbose_name = "Contact"
        verbose_name_plural = "List of contacts"
        ordering = ("-name",)
