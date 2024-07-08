import json

from rest_framework.exceptions import ValidationError

from .models import Category, Order, OrderItem, ProductInfo, Shop


def json_validator(obj):
    try:
        json_data = json.loads(obj)
    except json.JSONDecodeError:
        raise ValidationError("Incorrect request format")
    return json_data


def shop_state_validator(shop_ids):
    # Checking if any of the shops has the OFF status
    off_shops = Shop.objects.filter(id__in=shop_ids, state="off")
    if off_shops.exists():
        if len(off_shops.values_list("name", flat=True)) == 1:
            raise ValidationError(f"{off_shops.values_list('name', flat=True)[0]} shop is OFF")
        off_shops_names = ", ".join(off_shops.values_list("name", flat=True))
        raise ValidationError(f"{off_shops_names} shops are OFF")


def shop_category_validator(shop_id, category_id):
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


def basket_exists_validator(user):
    if not Order.objects.filter(user=user, status="basket").exists():
        raise ValidationError("You don't have an active basket")
    basket = Order.objects.get(user=user, status="basket")
    return basket


def product_in_basket_validator(basket, index_list):
    products = OrderItem.objects.filter(id__in=index_list, order=basket)

    # A dict for fast search of product by product_info
    product_dict = {product.id: product for product in products}

    valid_products_dict = {}
    missing_product_ids = []

    for index in index_list:
        product = product_dict.get(index)
        if not product:
            missing_product_ids.append(index)
        else:
            valid_products_dict[index] = product

    if missing_product_ids:
        if len(missing_product_ids) == 1:
            raise ValidationError(f"Product with id {missing_product_ids[0]} is not in the basket")
        missing_products_list = ", ".join(map(str, missing_product_ids))
        raise ValidationError(f"Products with ids {missing_products_list} are not in the basket")

    return valid_products_dict


class ProductValidators:
    def __init__(self, request_method, json_data, basket=None):
        self.json_data = json_data
        self.request_method = request_method
        self.valid_products_dict = {}
        self.basket = basket

    @property
    def search_param(self):
        if self.request_method == "POST":
            return "product_info"
        return "id"

    @property
    def query_request(self):
        if self.request_method == "POST":
            return ProductInfo.objects.filter
        return OrderItem.objects.filter

    def exist_validator(self):
        product_ids = {elem[self.search_param] for elem in self.json_data}

        match self.request_method:
            case "PATCH":
                products = self.query_request(id__in=product_ids, order=self.basket)
            case "POST":
                products = self.query_request(id__in=product_ids)

        product_dict = {product.id: product for product in products}

        valid_products_dict = {}
        missing_product_ids = []
        for index, elem in enumerate(self.json_data):
            product = product_dict.get(elem[self.search_param])
            if not product:
                missing_product_ids.append(elem[self.search_param])
            else:
                valid_products_dict[index] = product

        if missing_product_ids:
            if self.request_method == "POST":
                match len(missing_product_ids):
                    case 1:
                        raise ValidationError(
                            f"Product with id {missing_product_ids[0]} does not exist"
                        )
                    case _:
                        missing_products_list = ", ".join(map(str, missing_product_ids))
                        raise ValidationError(
                            f"Products with ids {missing_products_list} do not exist"
                        )

            else:
                match len(missing_product_ids):
                    case 1:
                        raise ValidationError(
                            f"Product with id {missing_product_ids[0]} is not in the basket"
                        )
                    case _:
                        missing_products_list = ", ".join(map(str, missing_product_ids))
                        raise ValidationError(
                            f"Products with ids {missing_products_list} are not in the basket"
                        )

        self.valid_products_dict = valid_products_dict

        return self.valid_products_dict

    def quantity_validator(self):
        missing_products = []

        for index, elem in enumerate(self.json_data):
            product = self.valid_products_dict.get(index)

            match self.request_method:
                case "POST":
                    if product.quantity < elem["quantity"]:
                        missing_products.append(elem[self.search_param])
                case "PATCH":
                    if product.product_info.quantity < elem["quantity"]:
                        missing_products.append(elem[self.search_param])

        if missing_products:
            if len(missing_products) == 1:
                raise ValidationError(f"Not enough product with id {missing_products[0]} in stock")
            missing_products_list = ", ".join(map(str, missing_products))
            raise ValidationError(f"Not enough products with ids {missing_products_list} in stock")

        return self.valid_products_dict
