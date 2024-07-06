import requests
import yaml
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import URLValidator
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Category,
    Contact,
    Order,
    OrderItem,
    Parameter,
    Product,
    ProductInfo,
    ProductParameter,
    Shop,
)
from .permissions import (
    EmailOrTokenPermission,
    EmailPasswordPermission,
    OnlyShopPermission,
)
from .serializers import (
    CategorySerializer,
    ContactSerializer,
    GetBasketSerializer,
    OrderSerializer,
    ProductSerializer,
    RegisterUserSerializer,
    ShopSerializer,
    UserSerializer,
)
from .validators import (
    basket_exists_validator,
    json_validator,
    product_basket_quantity_validator,
    product_in_basket_validator,
    product_shop_validator,
    shop_category_validator,
    shop_state_validator,
)


class RegisterUser(APIView):
    """
    Class for user registration.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterUserSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user = serializer.save()
            user.set_password(request.data["password"])
            user.save()
            return Response(
                {"message": "User created successfully"}, status=status.HTTP_201_CREATED
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class Login(APIView):
    """
    Class to achieve Token by provided user's email and password.
    """

    permission_classes = [EmailPasswordPermission]

    def post(self, request):
        user = request.user
        token, created = Token.objects.get_or_create(user=user)
        return Response({"token": token.key}, status=status.HTTP_201_CREATED)


class ManageContact(APIView):
    """
    Class for contact reading, creation, updating and deletion.
    """

    permission_classes = [EmailOrTokenPermission]

    def get(self, request):
        user_contact = Contact.objects.get(user=request.user)
        serializer = ContactSerializer(user_contact)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        request.data._mutable = True
        request.data.update({"user": request.user.id})
        serializer = ContactSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(
                {"message": "Contact created successfully"}, status=status.HTTP_201_CREATED
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        contact = get_object_or_404(Contact, user=request.user)
        serializer = ContactSerializer(contact, data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response({"message": "Contact updated successfully"}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        contact = get_object_or_404(Contact, user=request.user)
        contact.delete()
        return Response(
            {"message": "Contacts deleted successfully"}, status=status.HTTP_204_NO_CONTENT
        )


class ManageUserAccount(APIView):
    """
    Class for user account reading, updating and deletion.
    """

    permission_classes = [EmailOrTokenPermission]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response({"message": "User updated successfully"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class PartnerUpdate(APIView):
    """
    Class for partner updating.
    """

    permission_classes = [EmailOrTokenPermission]

    def post(self, request):
        user = request.user

        if user.type != "shop":
            return Response({"message": "Only for shops"}, status=status.HTTP_403_FORBIDDEN)
        url = request.data.get("url")

        if not url:
            return Response(
                {"error": "URL parameter is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            url_validator = URLValidator()
            url_validator(url)
        except DjangoValidationError as error:
            return Response({"Error": str(error.message)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            response = requests.get(url)
            response.raise_for_status()
            yml_file = response.content
            yaml_data = yaml.safe_load(yml_file)
        except requests.RequestException as error:
            return Response(
                {"error": f"Failed to fetch YAML data: {error}"}, status=status.HTTP_400_BAD_REQUEST
            )
        except yaml.YAMLError as error:
            return Response({"Error": str(error)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            shop_name = yaml_data.get("shop")
            shop_url = yaml_data.get("url")

            with transaction.atomic():
                shop, created = Shop.objects.get_or_create(name=shop_name, url=shop_url, user=user)

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
                                product_info=prod_info_obj, parameter=param_obj, value=value
                            )
        except Exception as error:
            return Response(
                {"error": f"Failed to update goods list: {error}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({"message": "Goods list updated successfully"}, status=status.HTTP_200_OK)


class PartnerState(APIView):
    """
    Class for partner state updating and reading.
    """

    permission_classes = [EmailOrTokenPermission, OnlyShopPermission]

    def get(self, request):
        user = request.user
        return Response(
            {"message": f"Shop state is {user.user_shop.state.upper()}"}, status=status.HTTP_200_OK
        )

    def patch(self, request):
        serializer = ShopSerializer(request.user.user_shop, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(
                {"message": "Shop state updated successfully"}, status=status.HTTP_200_OK
            )
        else:
            return Response({"message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class ManageOrder(APIView):
    """
    Class create and get orders.
    """

    permission_classes = [EmailOrTokenPermission]

    def get(self, request):
        orders = Order.objects.filter(user=request.user)
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        try:
            basket = basket_exists_validator(request.user)
        except DRFValidationError as e:
            raise DRFValidationError({"error": e.args[0]})
        basket.status = "placed"
        basket.save()
        return Response(
            {"message": "Order created successfully", "order_id": basket.id},
            status=status.HTTP_201_CREATED,
        )


class ProductsList(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        shop_id = request.query_params.get("shop_id")
        category_id = request.query_params.get("category_id")

        if shop_id and category_id:
            try:
                shop, category = shop_category_validator(shop_id, category_id)
                shop_state_validator([shop.id])
            except DRFValidationError as e:
                raise DRFValidationError({"error": e.args[0]})

            products = Product.objects.filter(
                category=category, product_infos__shop=shop
            ).distinct()
            if products:
                serializer = ProductSerializer(products, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response({"message": "no products found"}, status=status.HTTP_204_NO_CONTENT)
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ManageBasket(APIView):
    permission_classes = [EmailOrTokenPermission]

    def get(self, request):
        basket = Order.objects.filter(user=request.user, status="basket")
        serializer = GetBasketSerializer(basket, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        items = request.data.get("items")

        try:
            json_data = json_validator(items)
        except DRFValidationError as e:
            raise DRFValidationError({"error": e.args[0]})

        if all([{"product_info", "quantity"}.issubset(elem.keys()) for elem in json_data]):
            try:
                products_dict = product_shop_validator(json_data)
            except DRFValidationError as e:
                raise DRFValidationError({"error": e.args[0]})
            order, _ = Order.objects.get_or_create(user=request.user, status="basket")
            for index, elem in enumerate(json_data):
                product_info = products_dict.get(index)
                if product_info:
                    OrderItem.objects.create(
                        order=order,
                        product=product_info.product,
                        quantity=elem["quantity"],
                        shop=product_info.shop,
                    )
            if len(products_dict) == 1:
                return Response(
                    {"message": "Product has been successfully added to basket"},
                    status=status.HTTP_201_CREATED,
                )
            return Response(
                {"message": "Products have been successfully added to basket"},
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {"message": "Following parameters are required: product_info, quantity"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def patch(self, request, *args, **kwargs):
        items = request.data.get("items")

        try:
            json_data = json_validator(items)
        except DRFValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        if all([{"id", "quantity"}.issubset(elem.keys()) for elem in json_data]):
            try:
                basket = basket_exists_validator(request.user)
            except DRFValidationError as e:
                raise DRFValidationError({"error": e.args[0]})

            try:
                index_list = [elem["id"] for elem in json_data]
                valid_product_dict = product_in_basket_validator(basket, index_list)
                valid_products_quantity_dict = product_basket_quantity_validator(
                    valid_product_dict, json_data
                )

                for index, elem in valid_products_quantity_dict.items():
                    order_item = valid_products_quantity_dict.get(index)
                    order_item.quantity = json_data[index]["quantity"]
                    order_item.save()

                return Response(
                    {"message": "Basket has been successfully updated"}, status=status.HTTP_200_OK
                )

            except DRFValidationError as e:
                raise DRFValidationError({"error": e.args[0]})

        return Response(
            {"message": "Following parameters are required: id, quantity"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request):
        items = request.data.get("items")
        try:
            index_list = list(map(int, items.split(",")))
        except ValueError:
            return Response(
                {"error": "Incorrect request format"}, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            basket = Order.objects.get(user=request.user, status="basket")
        except Order.DoesNotExist:
            return Response(
                {"error": "You don't have active basket"}, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            valid_product_dict = product_in_basket_validator(basket, index_list)
        except DRFValidationError as e:
            raise DRFValidationError({"error": e.args[0]})

        indexes_to_delete = list(valid_product_dict.keys())

        order_items_to_delete = OrderItem.objects.filter(id__in=indexes_to_delete)

        order_items_to_delete.delete()

        if len(valid_product_dict) == 1:
            return Response(
                {"message": "Product has been successfully deleted from basket"},
                status=status.HTTP_204_NO_CONTENT,
            )
        return Response(
            {"message": "Products have been successfully deleted from basket"},
            status=status.HTTP_204_NO_CONTENT,
        )


class ShopList(ListAPIView):
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer
    permission_classes = [AllowAny]


class CategoryList(ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
