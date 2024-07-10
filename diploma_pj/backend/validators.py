import json
from typing import Union, List, Dict, Tuple, Optional

from django.db.models import Q, QuerySet
from rest_framework.exceptions import ValidationError

from .models import Category, Contact, Order, OrderItem, ProductInfo, Shop, User


def json_validator(obj: str) -> List[Dict[str, str]]:
    try:
        json_data = json.loads(obj)
    except json.JSONDecodeError:
        raise ValidationError("Incorrect request format")
    return json_data


def shop_state_validator(shop_ids: list[str]) -> None:
    # Checking if any of the shops has the OFF status
    off_shops = Shop.objects.filter(id__in=shop_ids, state="off")
    if off_shops.exists():
        if len(off_shops.values_list("name", flat=True)) == 1:
            raise ValidationError(f"{off_shops.values_list('name', flat=True)[0]} shop is OFF")
        off_shops_names = ", ".join(off_shops.values_list("name", flat=True))
        raise ValidationError(f"{off_shops_names} shops are OFF")


def shop_category_validator(shop_id: str, category_id: str) -> Tuple[Shop, Category]:
    # Check if shop exists
    if not Shop.objects.filter(id=shop_id).exists():
        raise ValidationError(f"Shop with id {shop_id} does not exist")

    # Check if category exists
    if not Category.objects.filter(external_id=category_id).exists():
        raise ValidationError(f"Category with id {category_id} does not exist")

    # Get the actual objects
    shop: Shop = Shop.objects.get(id=shop_id)
    category: Category = Category.objects.get(external_id=category_id)

    return shop, category


def basket_exists_validator(user: User) -> Order:
    if not Order.objects.filter(user=user, status="basket").exists():
        raise ValidationError("You don't have an active basket")
    basket: Order = Order.objects.get(user=user, status="basket")
    return basket


def contact_exists_validator(user: User, contact_ids: List[int]) -> Dict[int, Contact]:
    if not Contact.objects.filter(user=user).exists():
        raise ValidationError("You don't have any contacts")

    contacts: QuerySet[Union[Contact, None]] = Contact.objects.filter(user=user, id__in=contact_ids)

    contacts_dict: Dict[int, Contact] = {contact.id: contact for contact in contacts}

    valid_contact_dict: Dict[int, Contact] = {}
    missing_contact_ids: List[int] = []

    for index in contact_ids:
        contact = contacts_dict.get(index)
        if not contact:
            missing_contact_ids.append(index)
        else:
            valid_contact_dict[index] = contact

    if missing_contact_ids:
        match len(missing_contact_ids):
            case 1:
                raise ValidationError(
                    f"Contact with id {missing_contact_ids[0]} does not exist for this user"
                )
            case _:
                missing_products_list = ", ".join(map(str, missing_contact_ids))
                raise ValidationError(
                    f"Contacts with ids {missing_products_list} do not exist for this user"
                )
    return valid_contact_dict


class ProductValidators:
    def __init__(
        self,
        request_method: str,
        json_data: dict | list = None,
        basket: Optional[Order] = None,
        index_list: list[int] = None,
    ):
        self.json_data = json_data
        self.request_method = request_method
        self.valid_products_dict: Dict[int, Union[ProductInfo, OrderItem]] = {}
        self.basket = basket
        self.index_list = index_list

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

    def exist_validator(self) -> Dict[int, Union[ProductInfo, OrderItem]]:
        if self.json_data:
            product_ids = {elem[self.search_param] for elem in self.json_data}

        match self.request_method:
            case "POST":
                products = self.query_request(id__in=product_ids)
            case "PATCH":
                products = self.query_request(id__in=product_ids, order=self.basket)
            case "DELETE":
                products = self.query_request(id__in=self.index_list, order=self.basket)

        product_dict = {product.id: product for product in products}

        valid_products_dict = {}
        missing_product_ids = []

        match self.request_method:
            case "POST" | "PATCH":
                for index, elem in enumerate(self.json_data):
                    product = product_dict.get(elem[self.search_param])
                    if not product:
                        missing_product_ids.append(elem[self.search_param])
                    else:
                        valid_products_dict[index] = product

            case "DELETE":
                for index in self.index_list:
                    product = product_dict.get(index)
                    if not product:
                        missing_product_ids.append(index)
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

    def quantity_validator(self) -> Dict[int, Union[ProductInfo, OrderItem]]:
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


def already_ordered_products_validator(order: Order, json_data: List[Dict[str, str]]) -> None:
    product_infos = [int(elem["product_info"]) for elem in json_data]
    query_obj = Q(order=order) & Q(product_info__in=product_infos)
    if OrderItem.objects.filter(query_obj).exists():
        raise ValidationError("Products already in the basket")
