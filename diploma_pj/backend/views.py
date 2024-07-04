import requests
import yaml
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.http import JsonResponse
from rest_framework.authtoken.models import Token
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from .models import (
    Category,
    Contact,
    Order,
    Parameter,
    Product,
    ProductInfo,
    ProductParameter,
    Shop,
    User,
)
from .permissions import (
    EmailOrTokenPermission,
    EmailPasswordPermission,
    OnlyShopPermission,
)
from .serializers import (
    CategorySerializer,
    ContactCreateSerializer,
    ContactRetrieveSerializer,
    ContactUpdateSerializer,
    OrderSerializer,
    ProductSerializer,
    RegisterUserSerializer,
    ShopSerializer,
    UserSerializer,
    UserUpdateSerializer,
)


class Login(APIView):
    """
    Class to achieve Token by provided user's email and password.
    """

    permission_classes = [EmailPasswordPermission]

    def post(self, request, *args, **kwargs):
        user = request.user
        token, created = Token.objects.get_or_create(user=user)
        return JsonResponse({"token": token.key})


class RegisterUser(APIView):
    """
    Class for user registration.
    """

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = RegisterUserSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user = serializer.save()
            user.set_password(request.data["password"])
            user.save()
            return JsonResponse({"message": "User created successfully"})


class ManageContact(APIView):
    """
    Class for contact reading, creation, updating and deletion.
    """

    permission_classes = [EmailOrTokenPermission]

    def get(self, request, *args, **kwargs):
        user_contacts = Contact.objects.filter(user=request.user)
        serializer = ContactRetrieveSerializer(user_contacts, many=True)
        return JsonResponse(serializer.data, safe=False)

    def post(self, request):
        serializer = ContactCreateSerializer(data=request.data, context={"user": request.user})
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return JsonResponse({"message": "Contact created successfully"})
        else:
            return JsonResponse({"message": serializer.errors})

    def patch(self, request, *args, **kwargs):
        serializer = ContactUpdateSerializer(data=request.data, context={"user": request.user})
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return JsonResponse({"message": "Contact updated successfully"})
        else:
            return JsonResponse({"message": serializer.errors})

    def delete(self, request, *args, **kwargs):
        Contact.objects.filter(user=request.user).delete()
        return JsonResponse({"message": "Contacts deleted successfully"})


class ManageUserAccount(APIView):
    """
    Class for user account reading, updating and deletion.
    """

    permission_classes = [EmailOrTokenPermission]

    def get(self, request, *args, **kwargs):
        user = User.objects.get(email=request.user.email)
        serializer = UserSerializer(user)
        return JsonResponse(serializer.data, safe=False)

    def patch(self, request, *args, **kwargs):
        serializer = UserUpdateSerializer(data=request.data, context={"email": request.user.email})
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return JsonResponse({"message": "User updated successfully"})
        else:
            return JsonResponse({"message": serializer.errors})


class PartnerUpdate(APIView):
    """
    Class for partner updating.
    """

    permission_classes = [EmailOrTokenPermission]

    def post(self, request, *args, **kwargs):
        user = request.user
        if user.type != "shop":
            return JsonResponse({"message": "Only for shops"}, status=403)
        url = request.data.get("url")
        if url:
            url_validator = URLValidator()
            try:
                url_validator(url)
            except ValidationError as error:
                return JsonResponse({"Error": str(error)}, status=400)

            response = requests.get(url)
            yml_file = response.content

            try:
                yaml_data = yaml.safe_load(yml_file)
            except yaml.YAMLError as error:
                return JsonResponse({"Error": str(error)}, status=400)

            shop_name = yaml_data.get("shop")
            shop_url = yaml_data.get("url")

            shop, _ = Shop.objects.get_or_create(name=shop_name, url=shop_url, user=user)

            ProductInfo.objects.filter(shop=shop).delete()
            for elem in yaml_data.get("categories"):
                category, _ = Category.objects.get_or_create(
                    external_id=elem["id"], name=elem["name"]
                )
                category.shops.set([shop])
                category.save()

                filtered_by_category_goods = list(
                    filter(lambda x: x["category"] == category.external_id, yaml_data.get("goods"))
                )

                for item in filtered_by_category_goods:
                    product, _ = Product.objects.get_or_create(name=item["name"], category=category)
                    prod_info_obj = ProductInfo.objects.create(
                        product=product,
                        shop=shop,
                        quantity=item["quantity"],
                        price=item["price"],
                        price_rrc=item["price_rrc"],
                        external_id=item["id"],
                    )

                    for key, value in item["parameters"].items():
                        param_obj, _ = Parameter.objects.get_or_create(name=key)
                        ProductParameter.objects.create(
                            product_info=prod_info_obj, parameter=param_obj, value=value
                        )

        return JsonResponse({"message": "Goods list updated successfully"})


class PartnerState(APIView):
    """
    Class for partner state updating and reading.
    """

    permission_classes = [EmailOrTokenPermission, OnlyShopPermission]

    def get(self, request, *args, **kwargs):
        user = request.user
        return JsonResponse({"shop_state": user.user_shop.state})

    def patch(self, request, *args, **kwargs):
        serializer = ShopSerializer(data=request.data, context={"user": request.user})
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return JsonResponse({"message": "Shop state updated successfully"})
        else:
            return JsonResponse({"message": serializer.errors})


class ManageOrder(APIView):
    """
    Class create and get orders.
    """

    permission_classes = [EmailOrTokenPermission]

    def get(self, request, *args, **kwargs):
        orders = Order.objects.filter(user=request.user)
        serializer = OrderSerializer(orders, many=True)
        return JsonResponse(serializer.data, safe=False)

    def post(self, request, *args, **kwargs):
        serializer = OrderSerializer(data=request.data, context={"user": request.user})
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return JsonResponse(
                {"message": "Order created successfully", "order_id": serializer.data["id"]}
            )
        else:
            return JsonResponse({"message": serializer.errors})


class ProductsList(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        shop_id = request.query_params.get("shop_id")
        category_id = request.query_params.get("category_id")

        if shop_id and category_id:
            try:
                shop = Shop.objects.get(id=shop_id)
                category = Category.objects.get(external_id=category_id)
            except Shop.DoesNotExist:
                return JsonResponse({"message": "Shop does not exist"}, status=400)
            except Category.DoesNotExist:
                return JsonResponse({"message": "Category does not exist"}, status=400)

            products = Product.objects.filter(
                category=category, product_infos__shop=shop
            ).distinct()
            if products:
                serializer = ProductSerializer(products, many=True)
                return JsonResponse(serializer.data, safe=False)
            return JsonResponse({"message": "no products found"}, status=200)
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return JsonResponse(serializer.data, safe=False)


class ManageBusket(APIView):
    permission_classes = [EmailOrTokenPermission]

    def get(self, request, *args, **kwargs):
        pass

    def post(self, request, *args, **kwargs):
        pass

    def patch(self, request, *args, **kwargs):
        pass

    def delete(self, request, *args, **kwargs):
        pass

class ShopList(ListAPIView):
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer
    permission_classes = [AllowAny]


class CategoryList(ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
