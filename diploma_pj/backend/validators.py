import json

from django.core.validators import RegexValidator
from django.http import JsonResponse
from rest_framework.exceptions import ValidationError

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
    except ValueError:
        return JsonResponse({"Errors": "Incorrect request format"})
    return json_data


def product_available_validator(json_data):
    from .models import ProductInfo

    products_list = []
    for elem in json_data:
        try:
            product = ProductInfo.objects.get(shop=elem["shop"], id=elem["product_info"])
        except ProductInfo.DoesNotExist:
            raise ValidationError("Product is not available in this shop")
        if product.quantity < elem["quantity"]:
            raise ValidationError("Not enough product in stock")
        products_list.append(product)
    return products_list
