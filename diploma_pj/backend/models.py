from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .validators import phone_validator

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


class User(AbstractBaseUser):
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
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UserManager()

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    # def check_password(self, raw_password):
    #     return check_password(raw_password, self.password)
    #
    # def set_password(self, raw_password):
    #     self.password = make_password(raw_password, hasher="bcrypt_sha256")

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

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="User", related_name="contacts"
    )
    phone = models.CharField(
        max_length=20,
        verbose_name="Phone",
        unique=True,
        validators=[
            phone_validator,
        ],
    )
    city = models.CharField(max_length=100, verbose_name="City", blank=True)
    street = models.CharField(max_length=100, verbose_name="Street", blank=True)
    house = models.CharField(max_length=100, verbose_name="House", blank=True)
    structure = models.CharField(max_length=100, verbose_name="Structure", blank=True)
    building = models.CharField(max_length=100, verbose_name="Building", blank=True)
    apartment = models.CharField(max_length=100, verbose_name="Apartment", blank=True)

    class Meta:
        verbose_name = "Contact"
        verbose_name_plural = "List of contacts"
