import json

from django.core.validators import RegexValidator
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

phone_validator = RegexValidator(
    regex=r"^\+?1?\d{9,15}$",
    message="Phone number must be entered in the format: " "'+999999999'. Up to 15 digits allowed.",
)

city_name_validator = RegexValidator(
    regex=r"^[a-zA-Z\s-]+$",
    message="City name is not a valid. Only letters, spaces, and hyphens are allowed.",
)


def json_validator(obj):
    try:
        json_data = json.loads(obj)
        if not isinstance(json_data, dict | list):
            raise ValueError("Invalid JSON format")
    except (json.JSONDecodeError, ValueError):
        return Response({"error": "Incorrect request format"}, status=status.HTTP_400_BAD_REQUEST)
    return json_data


def shop_state_validator(shop_ids):
    from .models import Shop

    # Checking if any of the shops has the OFF status
    off_shops = Shop.objects.filter(id__in=shop_ids, state="off")
    if off_shops.exists():
        if len(off_shops.values_list("name", flat=True)) == 1:
            raise ValidationError(f"{off_shops.values_list('name', flat=True)[0]} shop is OFF")
        off_shops_names = ", ".join(off_shops.values_list("name", flat=True))
        raise ValidationError(f"{off_shops_names} shops are OFF")


def product_exist_validator(json_data):
    from .models import ProductInfo

    product_ids = {elem["product_info"] for elem in json_data}

    # Fetching products based on product_info IDs
    products = ProductInfo.objects.filter(id__in=product_ids)

    # A dict for fast search of product by product_info
    product_dict = {product.id: product for product in products}

    valid_products_dict = {}
    missing_product_ids = []
    for index, elem in enumerate(json_data):
        product = product_dict.get(elem["product_info"])
        if not product:
            missing_product_ids.append(elem["product_info"])
        else:
            valid_products_dict[index] = product

    if missing_product_ids:
        if len(missing_product_ids) == 1:
            raise ValidationError(f"Product with id {missing_product_ids[0]} does not exist")
        missing_products_list = ", ".join(map(str, missing_product_ids))
        raise ValidationError(f"Products with ids {missing_products_list} do not exist")

    return valid_products_dict


def product_quantity_validator(valid_products_dict, json_data):
    missing_products = []

    for index, elem in enumerate(json_data):
        product = valid_products_dict.get(index)
        if product and product.quantity < elem["quantity"]:
            missing_products.append(elem["product_info"])

    if missing_products:
        if len(missing_products) == 1:
            raise ValidationError(f"Not enough product with id {missing_products[0]} in stock")
        missing_products_list = ", ".join(map(str, missing_products))
        raise ValidationError(f"Not enough products with ids {missing_products_list} in stock")

    return valid_products_dict


def product_shop_validator(json_data):
    valid_products_dict = product_exist_validator(json_data)
    valid_products_dict = product_quantity_validator(valid_products_dict, json_data)

    # Extract shop_ids for shop state validation
    shop_ids = {product.shop_id for product in valid_products_dict.values()}

    # Validate shop states
    shop_state_validator(shop_ids)

    return valid_products_dict


def shop_category_validator(shop_id, category_id):
    from .models import Category, Shop

    # Check if shop exists
    if not Shop.objects.filter(id=shop_id).exists():
        raise ValidationError(f"Shop with id {shop_id} does not exist")

    # Check if category exists
    if not Category.objects.filter(external_id=category_id).exists():
        raise ValidationError(f"Category with id {category_id} does not exist")

    # Get the actual objects
    shop = Shop.objects.get(id=shop_id)
    category = Category.objects.get(external_id=category_id)

    return shop, category
