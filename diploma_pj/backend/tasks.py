import requests
import yaml
from celery import shared_task
from django.db import transaction

from .models import Category, Parameter, Product, ProductInfo, ProductParameter, Shop


@shared_task
def update_goods_list(user_id, url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        yml_file = response.content
        yaml_data = yaml.safe_load(yml_file)

        shop_name = yaml_data.get("shop")
        shop_url = yaml_data.get("url")

        with transaction.atomic():
            shop, created = Shop.objects.get_or_create(
                name=shop_name, url=shop_url, user_id=user_id
            )

            ProductInfo.objects.filter(shop=shop).delete()

            for category_data in yaml_data.get("categories", []):
                category, _ = Category.objects.get_or_create(
                    external_id=category_data.get("id"),
                    defaults={"name": category_data.get("name")},
                )
                category.shops.add(shop)

                goods_list = yaml_data.get("goods", [])
                filtered_goods = [
                    item for item in goods_list if item.get("category") == category.external_id
                ]

                for item in filtered_goods:
                    product, _ = Product.objects.get_or_create(
                        name=item.get("name"), category=category
                    )
                    prod_info_obj = ProductInfo.objects.create(
                        product=product,
                        shop=shop,
                        quantity=item.get("quantity"),
                        price=item.get("price"),
                        price_rrc=item.get("price_rrc"),
                        external_id=item.get("id"),
                    )

                    for key, value in item.get("parameters", {}).items():
                        param_obj, _ = Parameter.objects.get_or_create(name=key)
                        ProductParameter.objects.create(
                            product_info=prod_info_obj,
                            parameter=param_obj,
                            value=value,
                            product=product,
                        )
    except Exception as e:
        raise e
