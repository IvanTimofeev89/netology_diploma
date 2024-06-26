from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    Group,
    Permission,
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone

# Choices for the status of an order
STATUS_CHOICES = (
    ("new", "New"),
    ("confirmed", "Confirmed"),
    ("assembled", "Assembled"),
    ("sent", "Sent"),
    ("delivered", "Delivered"),
    ("canceled", "Canceled"),
    ("returned", "Returned"),
)

# Choices for the type of contact
CONTACT_TYPES = (
    ("shop", "Shop"),
    ("buyer", "Buyer"),
)


class UserManager(BaseUserManager):
    """
    Custom manager for the User model, providing methods to create regular users and superusers.
    """

    def create_user(self, email, first_name, last_name, family_name, password=None, **extra_fields):
        """
        Create and save a regular user with the given email,
        first name, last name, family name, and password.

        :param email: The email address of the user.
        :param first_name: The first name of the user.
        :param last_name: The last name of the user.
        :param family_name: The family name of the user.
        :param password: The password for the user.
        :param extra_fields: Additional fields to be saved for the user.
        :return: The created user.
        """
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            first_name=first_name,
            last_name=last_name,
            family_name=family_name,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self, email, first_name, last_name, family_name, password=None, **extra_fields
    ):
        """
        Create and save a superuser with the given email,
        first name, last name, family name, and password.

        :param email: The email address of the superuser.
        :param first_name: The first name of the superuser.
        :param last_name: The last name of the superuser.
        :param family_name: The family name of the superuser.
        :param password: The password for the superuser.
        :param extra_fields: Additional fields to be saved for the superuser.
        :return: The created superuser.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        return self.create_user(email, first_name, last_name, family_name, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Model to override standard django User model with additional fields.
    """

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    family_name = models.CharField(max_length=30)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    groups = models.ManyToManyField(
        Group, verbose_name="groups", blank=True, related_name="custom_user_groups"
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name="user permissions",
        blank=True,
        related_name="custom_user_permissions",
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "family_name"]

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"


class Shop(models.Model):
    """
    Model representing a shop.
    """

    name = models.CharField(max_length=100, verbose_name="Shop name")
    url = models.URLField(null=True, blank=True, verbose_name="Shop URL")

    class Meta:
        verbose_name = "Shop"
        verbose_name_plural = "List of shops"
        ordering = ("-name",)


class Category(models.Model):
    """
    Model representing a category.
    """

    shops = models.ManyToManyField(Shop, verbose_name="Shops", related_name="categories")
    name = models.CharField(max_length=100, verbose_name="Category name")

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "List of categories"
        ordering = ("-name",)


class Product(models.Model):
    """
    Model representing a product.
    """

    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=100, verbose_name="Product name")

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "List of products"
        ordering = ("-name",)


class ProductInfo(models.Model):
    """
    Model representing product information.
    """

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, verbose_name="Product", related_name="product_infos"
    )
    shop = models.ForeignKey(
        Shop, on_delete=models.CASCADE, verbose_name="Shop", related_name="shop_infos"
    )
    quantity = models.PositiveIntegerField(verbose_name="Quantity")
    price = models.PositiveIntegerField(verbose_name="Price")
    price_rrc = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Recommended retail price"
    )

    class Meta:
        verbose_name = "Product information"
        verbose_name_plural = "List of products information"


class Parameter(models.Model):
    """
    Model representing a parameter.
    """

    name = models.CharField(max_length=100, verbose_name="Parameter name")

    class Meta:
        verbose_name = "Parameter"
        verbose_name_plural = "List of parameters"
        ordering = ("-name",)


class ProductParameter(models.Model):
    """
    Model representing a product parameter.
    """

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
    """
    Model representing an order.
    """

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="User", related_name="orders"
    )
    date = models.DateField(verbose_name="Date", auto_now_add=True)
    status = models.CharField(
        choices=STATUS_CHOICES, default="new", verbose_name="Status", max_length=20
    )

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "List of orders"
        ordering = ("-date",)


class OrderItem(models.Model):
    """
    Model representing an ordered item.
    """

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
    """
    Model representing a contact.
    """

    type = models.CharField(choices=CONTACT_TYPES, verbose_name="Type", max_length=20)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="User", related_name="contacts"
    )
    name = models.CharField(max_length=100, verbose_name="Name")
    phone = models.CharField(max_length=20, verbose_name="Phone")
    city = models.CharField(max_length=100, verbose_name="City", default="n/a")
    street = models.CharField(max_length=100, verbose_name="Street", default="n/a")
    house = models.CharField(max_length=100, verbose_name="House", default="n/a")
    structure = models.CharField(max_length=100, verbose_name="Structure", blank=True)
    building = models.CharField(max_length=100, verbose_name="Building", blank=True)
    apartment = models.CharField(max_length=100, verbose_name="Apartment", blank=True)

    class Meta:
        verbose_name = "Contact"
        verbose_name_plural = "List of contacts"
