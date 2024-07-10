from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    Group,
    Permission,
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_rest_passwordreset.tokens import get_token_generator

from .regex_validators import city_name_validator, phone_validator

# Choices for the status of an order
STATUS_CHOICES = (
    ("new", "New"),
    ("confirmed", "Confirmed"),
    ("assembled", "Assembled"),
    ("placed", "Placed"),
    ("sent", "Sent"),
    ("delivered", "Delivered"),
    ("canceled", "Canceled"),
    ("returned", "Returned"),
    ("basket", "Basket"),
)

# Choices for the type of contact
CONTACT_TYPES = (
    ("shop", "Shop"),
    ("buyer", "Buyer"),
)

SHOP_STATES = (
    ("on", "ON"),
    ("off", "OFF"),
)


class UserManager(BaseUserManager):
    """
    Custom manager for the User model, providing methods to create regular users and superusers.
    """

    use_in_migrations = True

    def create_user(self, email, password, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError(_("The Email must be set"))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Model to override standard django User model with additional fields.
    """

    type = models.CharField(
        choices=CONTACT_TYPES, verbose_name="Type", max_length=20, default="buyer"
    )
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    middle_name = models.CharField(max_length=30, blank=True)
    company = models.CharField(max_length=100, blank=True)
    position = models.CharField(max_length=100, blank=True)
    is_email_confirmed = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
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

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"


class Shop(models.Model):
    """
    Model representing a shop.
    """

    name = models.CharField(max_length=100, verbose_name="Shop name", null=True, blank=True)
    url = models.URLField(verbose_name="Shop URL", null=True, blank=True)
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, verbose_name="User", related_name="user_shop"
    )
    state = models.CharField(
        choices=SHOP_STATES, verbose_name="State of the shop", max_length=3, default="on"
    )

    class Meta:
        verbose_name = "Shop"
        verbose_name_plural = "Shops"
        ordering = ("-name",)

    def __str__(self):
        return self.name


class Category(models.Model):
    """
    Model representing a category.
    """

    shops = models.ManyToManyField(Shop, verbose_name="Shops", related_name="categories")
    external_id = models.PositiveIntegerField(verbose_name="External ID", blank=True)
    name = models.CharField(max_length=100, verbose_name="Category name")

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ("-name",)

    def __str__(self):
        return self.name


class Product(models.Model):
    """
    Model representing a product.
    """

    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=100, verbose_name="Product name")

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ("-name",)

    def __str__(self):
        return self.name


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
    external_id = models.PositiveIntegerField(verbose_name="External ID", blank=True)

    class Meta:
        verbose_name = "Product information"
        verbose_name_plural = "Product information"

    def __str__(self):
        return ""


class Parameter(models.Model):
    """
    Model representing a parameter.
    """

    name = models.CharField(max_length=100, verbose_name="Parameter name")

    class Meta:
        verbose_name = "Parameter"
        verbose_name_plural = "Parameters"
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
        verbose_name_plural = "Product parameters"


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
        verbose_name_plural = "Orders"
        ordering = ("-date",)

    def __str__(self):
        return f"Order №{self.id} - {self.user.email} - {self.date}"

    def save(self, *args, **kwargs):
        from .signals import order_status_changed

        if self.status != "basket":
            data = {"id": self.id, "status": self.status}

            order_status_changed.send(sender=self.__class__, user_id=self.user_id, data=data)
        super().save(*args, **kwargs)


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
        related_name="product_order_items",
    )
    shop = models.ForeignKey(
        Shop, on_delete=models.CASCADE, verbose_name="Shop", related_name="shop_items"
    )
    quantity = models.PositiveIntegerField(verbose_name="Quantity")
    product_info = models.ForeignKey(
        ProductInfo,
        on_delete=models.CASCADE,
        verbose_name="Product information",
        related_name="prod_info_order_items",
    )

    class Meta:
        verbose_name = "Ordered item"
        verbose_name_plural = "Ordered items"
        constraints = [
            models.UniqueConstraint(fields=["order_id", "product_info"], name="unique_order_item"),
        ]

    def __str__(self):
        return str(self.product_info.id)


class Contact(models.Model):
    """
    Model representing a contact.
    """

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="User", related_name="contacts"
    )
    phone = models.CharField(
        max_length=20,
        verbose_name="Phone",
        validators=[
            phone_validator,
        ],
    )
    city = models.CharField(
        max_length=100,
        verbose_name="City",
        blank=True,
        validators=[
            city_name_validator,
        ],
    )
    street = models.CharField(max_length=100, verbose_name="Street", blank=True)
    house = models.CharField(max_length=10, verbose_name="House", blank=True)
    structure = models.CharField(max_length=10, verbose_name="Structure", blank=True)
    building = models.CharField(max_length=10, verbose_name="Building", blank=True)
    apartment = models.CharField(max_length=10, verbose_name="Apartment", blank=True)

    class Meta:
        verbose_name = "Contact"
        verbose_name_plural = "Contacts"


class ConfirmEmailToken(models.Model):
    """
    Model representing a confirmation email token.
    """

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="User", related_name="confirm_email_tokens"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    key = models.CharField(
        max_length=64, unique=True, db_index=True, verbose_name="Token for email confirmation"
    )

    class Meta:
        verbose_name = "Confirmation email token"
        verbose_name_plural = "Confirmation email tokens"

    def save(self, *args, **kwargs):
        if not self.key:
            token_generator = get_token_generator()
            self.key = token_generator.generate_token()
        super().save(*args, **kwargs)
