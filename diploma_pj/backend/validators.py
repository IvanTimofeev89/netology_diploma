import json

from django.core.validators import RegexValidator
from django.db.models import Q
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


def shop_validator(json_data):
    from .models import Shop

    shop_ids = {elem["shop"] for elem in json_data}

    # Checking if all requested shops exist
    existing_shops = Shop.objects.filter(id__in=shop_ids).values_list("id", "state")

    missing_shops = shop_ids - set([elem[0] for elem in existing_shops])
    if missing_shops:
        if len(missing_shops) == 1:
            raise ValidationError(f"Shop with id {list(missing_shops)[0]} does not exist")
        missing_shops_list = ", ".join(map(str, missing_shops))
        raise ValidationError(f"Shops with ids {missing_shops_list} do not exist")

    # Checking if any of the shops has the OFF status
    off_shops_id = set([shop[0] for shop in existing_shops if shop[1] == "off"])
    if off_shops_id:
        if len(off_shops_id) == 1:
            raise ValidationError(f"Shop with id {list(off_shops_id)[0]} is OFF")
        off_shops_list = ", ".join(map(str, off_shops_id))
        raise ValidationError(f"Shops with ids {off_shops_list} are OFF")


def product_validator(json_data):
    from .models import ProductInfo

    product_ids = {(elem["shop"], elem["product_info"]) for elem in json_data}

    # Products availability checking for each shop and its amount
    query = Q()
    for shop_id, product_id in product_ids:
        query |= Q(shop=shop_id, id=product_id)
    products = ProductInfo.objects.filter(query)

    # A dict for fast search of product by shop and product_info
    product_dict = {(product.shop_id, product.id): product for product in products}

    valid_products_list = []
    for index, elem in enumerate(json_data):
        product = product_dict.get((elem["shop"], elem["product_info"]))
        if not product:
            raise ValidationError(
                f"Product with id {elem['product_info']} in shop {elem['shop']} does not exist"
            )
        if product.quantity < elem["quantity"]:
            raise ValidationError(f"Not enough product with id {elem['product_info']} in stock")
        valid_products_list.append((index, product))

    # List sorting according to index
    valid_products_list.sort(key=lambda x: x[0])

    # Return list of products with index
    return [product for index, product in valid_products_list]


def product_shop_validator(json_data):
    shop_validator(json_data)
    valid_products = product_validator(json_data)
    return valid_products


def shop_category_exist(shop_id, category_id):
    from .models import Category, Shop

    try:
        shop_exists = Shop.objects.filter(id=shop_id).exists()
        category_exists = Category.objects.filter(external_id=category_id).exists()

        if not shop_exists:
            raise ValidationError({"error": f"Shop with id {shop_id} does not exist"})
        if not category_exists:
            raise ValidationError({"error": f"Category with id {category_id} does not exist"})

        shop = Shop.objects.get(id=shop_id)
        category = Category.objects.get(external_id=category_id)

        return shop, category

    except Shop.DoesNotExist:
        raise ValidationError({"error": f"Shop with id {shop_id} does not exist"})

    except Category.DoesNotExist:
        raise ValidationError({"error": f"Category with id {category_id} does not exist"})
