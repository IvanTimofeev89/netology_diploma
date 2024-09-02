from typing import Dict, List, Optional, Set

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import URLValidator
from django.db import transaction
from django.db.models import QuerySet
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiRequest,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import serializers, status
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView

from .models import (
    Category,
    ConfirmEmailToken,
    Contact,
    Order,
    OrderItem,
    Product,
    ProductInfo,
    Shop,
    User,
)
from .permissions import EmailOrTokenPermission, OnlyShopPermission
from .serializers import (
    CategorySerializer,
    ContactSerializer,
    ErrorResponseSerializer,
    GetBasketSerializer,
    OrderSerializer,
    ProductSerializer,
    RegisterUserSerializer,
    ShopSerializer,
    SuccessResponseSerializer,
    TokenSerializer,
    UserSerializer,
)
from .tasks import update_goods_list
from .validators import (
    ProductValidators,
    already_ordered_products_validator,
    basket_exists_validator,
    contact_exists_validator,
    json_validator,
    shop_category_validator,
    shop_state_validator,
)


class RegisterUser(APIView):
    """
    Class for user registration.

    """

    permission_classes = [AllowAny]

    @extend_schema(
        tags=["User"],
        request=RegisterUserSerializer,
        responses={
            status.HTTP_201_CREATED: SuccessResponseSerializer,
            status.HTTP_400_BAD_REQUEST: ErrorResponseSerializer,
        },
        examples=[
            OpenApiExample(
                "Example request",
                value={
                    "email": "test@mail.ru",
                    "password": "goodpassword",
                    "first_name": "test",
                    "last_name": "test",
                    "middle_name": "test",
                    "company": "test",
                    "position": "test",
                },
                request_only=True,
                response_only=False,
            )
        ],
        methods=["POST"],
    )
    def post(self, request: Request) -> Response:
        """
        Handle POST request to register a new user.

        Args:
            request (Request): The Django request object.

        Returns:
            Response: The response indicating the status of the operation and any errors.
        """
        serializer: RegisterUserSerializer = RegisterUserSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user: User = serializer.save()
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

    permission_classes = [EmailOrTokenPermission]
    throttle_classes = [UserRateThrottle]

    @extend_schema(
        tags=["User"],
        responses={
            status.HTTP_201_CREATED: TokenSerializer,
            status.HTTP_401_UNAUTHORIZED: ErrorResponseSerializer,
        },
        parameters=[
            OpenApiParameter(
                name="email",
                location=OpenApiParameter.HEADER,
                description="User's email",
                required=True,
                type=str,
            ),
            OpenApiParameter(
                name="password",
                location=OpenApiParameter.HEADER,
                description="User's password",
                required=True,
                type=str,
            ),
        ],
        methods=["POST"],
    )
    def post(self, request: Request) -> Response:
        """
        Handle POST request to log in a user and provide a token.
        Args:
            request (Request): The Django request object.

        Returns:
            Response: The response indicating the status of the operation and any errors.
        """
        user: User = request.user
        token, created = Token.objects.get_or_create(user=user)
        return Response({"token": token.key}, status=status.HTTP_201_CREATED)


class EmailConfirm(APIView):
    """
    Class to handle email confirmation.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        tags=["User"],
        request=inline_serializer(
            "body", fields={"token": serializers.CharField(), "email": serializers.EmailField()}
        ),
        responses={
            status.HTTP_200_OK: SuccessResponseSerializer,
            status.HTTP_400_BAD_REQUEST: ErrorResponseSerializer,
        },
        methods=["POST"],
    )
    def post(self, request: Request) -> Response:
        """
        Handle POST request to confirm user's email with a token.
        """
        token: Optional[str] = request.data.get("token")
        email: Optional[str] = request.data.get("email")
        if token and email:
            if not ConfirmEmailToken.objects.filter(key=token).exists():
                return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)

            key: Optional[ConfirmEmailToken] = ConfirmEmailToken.objects.filter(
                key=token, user__email=email
            ).first()
            if not key:
                return Response({"error": "Invalid email"}, status=status.HTTP_400_BAD_REQUEST)
            key.user.is_email_confirmed = True
            key.user.save()
            key.delete()
            return Response({"message": "Email confirmed successfully"}, status=status.HTTP_200_OK)
        return Response(
            {"error": "Token and email are required"}, status=status.HTTP_400_BAD_REQUEST
        )


@extend_schema(
    tags=["User"],
    parameters=[
        OpenApiParameter(
            name="token",
            location=OpenApiParameter.HEADER,
            description="User's token",
            required=True,
            type=str,
        ),
        OpenApiParameter(
            name="email",
            location=OpenApiParameter.HEADER,
            description="User's email",
            required=False,
            type=str,
        ),
        OpenApiParameter(
            name="password",
            location=OpenApiParameter.HEADER,
            description="User's password",
            required=False,
            type=str,
        ),
    ],
)
class ManageContact(APIView):
    """
    Class for contact reading, creation, updating and deletion.
    """

    permission_classes = [EmailOrTokenPermission]
    throttle_classes = [UserRateThrottle]

    @extend_schema(
        responses={
            status.HTTP_200_OK: ContactSerializer,
            status.HTTP_404_NOT_FOUND: ErrorResponseSerializer,
            status.HTTP_401_UNAUTHORIZED: ErrorResponseSerializer,
        },
        methods=["GET"],
    )
    def get(self, request: Request) -> Response:
        """
        Handle GET request to retrieve user's contacts.
        """
        if not Contact.objects.filter(user=request.user).exists():
            return Response(
                {"error": "You don't have any contacts"}, status=status.HTTP_404_NOT_FOUND
            )
        user_contact: QuerySet[Contact] = Contact.objects.filter(user=request.user)
        serializer: ContactSerializer = ContactSerializer(user_contact, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=ContactSerializer,
        responses={
            status.HTTP_201_CREATED: SuccessResponseSerializer,
            status.HTTP_400_BAD_REQUEST: ErrorResponseSerializer,
            status.HTTP_401_UNAUTHORIZED: ErrorResponseSerializer,
        },
        methods=["POST"],
    )
    def post(self, request: Request) -> Response:
        """
        Handle POST request to create a new contact for the user.
        """
        request.data._mutable = True
        request.data.update({"user": request.user.id})
        serializer: ContactSerializer = ContactSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(
                {"message": "Contact created successfully"}, status=status.HTTP_201_CREATED
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        request=ContactSerializer,
        responses={
            status.HTTP_200_OK: SuccessResponseSerializer,
            status.HTTP_400_BAD_REQUEST: ErrorResponseSerializer,
            status.HTTP_401_UNAUTHORIZED: ErrorResponseSerializer,
        },
        methods=["PATCH"],
    )
    def patch(self, request: Request) -> Response:
        """
        Handle PATCH request to update an existing contact.
        """
        contact_id: Optional[str] = request.data.get("id")
        if contact_id:
            try:
                contact_id = int(contact_id)
            except ValueError:
                return Response(
                    {"error": "Incorrect request format"}, status=status.HTTP_400_BAD_REQUEST
                )

            try:
                contact_dict: Dict[int, Contact] = contact_exists_validator(
                    request.user, [contact_id]
                )
            except DRFValidationError as e:
                raise DRFValidationError({"error": e.args[0]})

            contact: Contact = contact_dict.get(contact_id)
            serializer: ContactSerializer = ContactSerializer(
                contact, data=request.data, partial=True
            )
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return Response(
                    {"message": "Contact updated successfully"}, status=status.HTTP_200_OK
                )
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {"error": "You must provide contact ID"}, status=status.HTTP_400_BAD_REQUEST
        )

    @extend_schema(
        request=OpenApiRequest(
            inline_serializer(
                name="DeleteContactSerializer",
                fields={
                    "items": serializers.ListField(
                        child=serializers.IntegerField(), allow_empty=False
                    )
                },
            )
        ),
        responses={
            status.HTTP_204_NO_CONTENT: SuccessResponseSerializer,
            status.HTTP_400_BAD_REQUEST: ErrorResponseSerializer,
            status.HTTP_401_UNAUTHORIZED: ErrorResponseSerializer,
        },
        methods=["DELETE"],
    )
    def delete(self, request: Request) -> Response:
        """
        Handle DELETE request to delete user's contacts.
        """
        items: Optional[str] = request.data.get("items")
        if items:
            try:
                contact_ids_list: List[int] = list(map(int, items.split(",")))
            except ValueError:
                return Response(
                    {"error": "Incorrect request format"}, status=status.HTTP_400_BAD_REQUEST
                )

            try:
                contacts_ids_list: Dict[int, Contact] = contact_exists_validator(
                    request.user, contact_ids_list
                )
            except DRFValidationError as e:
                raise DRFValidationError({"error": e.args[0]})

            indexes_to_delete: List[int] = list(contacts_ids_list.keys())

            with transaction.atomic():
                contacts: QuerySet[Contact] = Contact.objects.filter(
                    user=request.user, id__in=indexes_to_delete
                )
                contacts.delete()

            if len(contact_ids_list) == 1:
                return Response(
                    {"message": "Contact deleted successfully"}, status=status.HTTP_204_NO_CONTENT
                )
            return Response(
                {"message": "Contacts deleted successfully"}, status=status.HTTP_204_NO_CONTENT
            )

        return Response(
            {"error": "You must provide ID of contacts"}, status=status.HTTP_400_BAD_REQUEST
        )


@extend_schema(
    tags=["User"],
    parameters=[
        OpenApiParameter(
            name="token",
            location=OpenApiParameter.HEADER,
            description="User's token",
            required=True,
            type=str,
        ),
        OpenApiParameter(
            name="email",
            location=OpenApiParameter.HEADER,
            description="User's email",
            required=False,
            type=str,
        ),
        OpenApiParameter(
            name="password",
            location=OpenApiParameter.HEADER,
            description="User's password",
            required=False,
            type=str,
        ),
    ],
)
class ManageUserAccount(APIView):
    """
    Class for user account reading, updating and deletion.
    """

    permission_classes = [EmailOrTokenPermission]
    throttle_classes = [UserRateThrottle]

    @extend_schema(
        responses={
            status.HTTP_200_OK: SuccessResponseSerializer,
            status.HTTP_401_UNAUTHORIZED: ErrorResponseSerializer,
        },
        methods=["GET"],
    )
    def get(self, request: Request) -> Response:
        """
        Handle GET request to retrieve user's account details.
        """
        serializer: UserSerializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=UserSerializer,
        responses={
            status.HTTP_200_OK: SuccessResponseSerializer,
            status.HTTP_401_UNAUTHORIZED: ErrorResponseSerializer,
            status.HTTP_400_BAD_REQUEST: ErrorResponseSerializer,
        },
        methods=["PATCH"],
    )
    def patch(self, request: Request) -> Response:
        """
        Handle PATCH request to update user's account details.
        """
        serializer: UserSerializer = UserSerializer(request.user, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response({"message": "User updated successfully"}, status=status.HTTP_200_OK)
        else:
            return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=["Partners"],
    parameters=[
        OpenApiParameter(
            name="token",
            location=OpenApiParameter.HEADER,
            description="User's token",
            required=True,
            type=str,
        ),
        OpenApiParameter(
            name="email",
            location=OpenApiParameter.HEADER,
            description="User's email",
            required=False,
            type=str,
        ),
        OpenApiParameter(
            name="password",
            location=OpenApiParameter.HEADER,
            description="User's password",
            required=False,
            type=str,
        ),
    ],
)
class PartnerUpdate(APIView):
    """
    Class for partner updating.
    """

    permission_classes = [EmailOrTokenPermission, OnlyShopPermission]
    throttle_classes = [UserRateThrottle]

    @extend_schema(
        request=inline_serializer("url", fields={"url": serializers.URLField()}),
        responses={
            status.HTTP_200_OK: SuccessResponseSerializer,
            status.HTTP_400_BAD_REQUEST: ErrorResponseSerializer,
            status.HTTP_401_UNAUTHORIZED: ErrorResponseSerializer,
            status.HTTP_403_FORBIDDEN: ErrorResponseSerializer,
        },
        methods=["POST"],
    )
    def post(self, request):
        user = request.user
        url = request.data.get("url")

        if not url:
            return Response(
                {"error": "URL parameter is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            url_validator = URLValidator()
            url_validator(url)
        except DjangoValidationError as error:
            return Response({"error": str(error.message)}, status=status.HTTP_400_BAD_REQUEST)

        update_goods_list.delay(user.id, url)

        return Response({"message": "Goods list update started"}, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Partners"],
    parameters=[
        OpenApiParameter(
            name="token",
            location=OpenApiParameter.HEADER,
            description="User's token",
            required=True,
            type=str,
        ),
        OpenApiParameter(
            name="email",
            location=OpenApiParameter.HEADER,
            description="User's email",
            required=False,
            type=str,
        ),
        OpenApiParameter(
            name="password",
            location=OpenApiParameter.HEADER,
            description="User's password",
            required=False,
            type=str,
        ),
    ],
)
class PartnerState(APIView):
    """
    Class for partner state updating and reading.
    Thees methods are allowed for authorized users with status 'shop'
    """

    permission_classes = [EmailOrTokenPermission, OnlyShopPermission]
    throttle_classes = [UserRateThrottle]

    @extend_schema(
        responses={
            status.HTTP_200_OK: SuccessResponseSerializer,
            status.HTTP_401_UNAUTHORIZED: ErrorResponseSerializer,
            status.HTTP_403_FORBIDDEN: ErrorResponseSerializer,
        },
        methods=["GET"],
    )
    def get(self, request: Request) -> Response:
        """
        Handle GET request to retrieve partner's state.
        """
        user: User = request.user
        return Response(
            {"message": f"Shop state is {user.user_shop.state.upper()}"}, status=status.HTTP_200_OK
        )

    @extend_schema(
        request=ShopSerializer,
        responses={
            status.HTTP_200_OK: SuccessResponseSerializer,
            status.HTTP_400_BAD_REQUEST: ErrorResponseSerializer,
            status.HTTP_401_UNAUTHORIZED: ErrorResponseSerializer,
            status.HTTP_403_FORBIDDEN: ErrorResponseSerializer,
        },
        methods=["PATCH"],
    )
    def patch(self, request: Request) -> Response:
        """
        Handle PATCH request to update partner's state.
        """
        serializer: ShopSerializer = ShopSerializer(request.user.user_shop, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(
                {"message": "Shop state updated successfully"}, status=status.HTTP_200_OK
            )
        else:
            return Response({"message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=["Shop"],
    parameters=[
        OpenApiParameter(
            name="token",
            location=OpenApiParameter.HEADER,
            description="User's token",
            required=True,
            type=str,
        ),
        OpenApiParameter(
            name="email",
            location=OpenApiParameter.HEADER,
            description="User's email",
            required=False,
            type=str,
        ),
        OpenApiParameter(
            name="password",
            location=OpenApiParameter.HEADER,
            description="User's password",
            required=False,
            type=str,
        ),
    ],
)
class ManageOrder(APIView):
    """
    Class to create and get orders.
    """

    permission_classes = [EmailOrTokenPermission]
    throttle_classes = [UserRateThrottle]

    @extend_schema(
        responses={
            status.HTTP_200_OK: OrderSerializer,
            status.HTTP_401_UNAUTHORIZED: ErrorResponseSerializer,
        },
        methods=["GET"],
    )
    def get(self, request: Request) -> Response:
        """
        Handle GET request to retrieve user's orders.
        """
        orders: QuerySet[Order] = Order.objects.filter(user=request.user)
        if orders:
            serializer: OrderSerializer = OrderSerializer(orders, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({"message": "You don't have any orders"}, status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        responses={
            status.HTTP_201_CREATED: inline_serializer(
                "body",
                fields={"message": serializers.CharField(), "order_id": serializers.IntegerField()},
            ),
            status.HTTP_401_UNAUTHORIZED: ErrorResponseSerializer,
            status.HTTP_403_FORBIDDEN: ErrorResponseSerializer,
        },
        methods=["POST"],
    )
    def post(self, request: Request) -> Response:
        """
        Handle POST request to create a new order from user's basket.
        """
        try:
            basket: Order = basket_exists_validator(request.user)
        except DRFValidationError as e:
            raise DRFValidationError({"error": e.args[0]})
        if not basket.user.is_email_confirmed:
            return Response(
                {"error": "Your email is not confirmed"},
                status=status.HTTP_403_FORBIDDEN,
            )
        basket.status = "placed"
        basket.save()
        return Response(
            {"message": "Order created successfully", "order_id": basket.id},
            status=status.HTTP_201_CREATED,
        )


@extend_schema_view(
    get=extend_schema(
        tags=["Shop"],
        responses={
            status.HTTP_200_OK: ProductSerializer(many=True),
            status.HTTP_204_NO_CONTENT: SuccessResponseSerializer,
            status.HTTP_400_BAD_REQUEST: ErrorResponseSerializer,
        },
        parameters=[
            OpenApiParameter(
                name="shop_id",
                location=OpenApiParameter.QUERY,
                description="Shop Id",
                required=False,
                type=int,
            ),
            OpenApiParameter(
                name="category_di",
                location=OpenApiParameter.QUERY,
                description="Category Id",
                required=False,
                type=int,
            ),
        ],
    )
)
class ProductsList(APIView):
    """
    Class to list products based on shop and category.
    """

    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]

    def get(self, request: Request) -> Response:
        """
        Handle GET request to retrieve products based on shop_id and category_id.
        """
        shop_id: Optional[str] = request.query_params.get("shop_id")
        category_id: Optional[str] = request.query_params.get("category_id")

        if shop_id and category_id:
            try:
                shop, category = shop_category_validator(shop_id, category_id)
                shop_state_validator([shop.id])
            except DRFValidationError as e:
                raise DRFValidationError({"error": e.args[0]})

            products: QuerySet[Product] = Product.objects.filter(
                category=category, product_infos__shop=shop
            ).distinct()
        else:
            products: QuerySet[Product] = Product.objects.filter(product_infos__shop__state="on")

        if not products.exists():
            return Response({"message": "no products found"}, status=status.HTTP_204_NO_CONTENT)

        paginator = PageNumberPagination()
        paginator.page_size = 10
        result_page = paginator.paginate_queryset(products, request)
        if not result_page:
            return Response({"message": "no products found"}, status=status.HTTP_204_NO_CONTENT)

        serializer: ProductSerializer = ProductSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)


class ManageBasket(APIView):
    """
    Class to manage user's basket.
    """

    permission_classes = [EmailOrTokenPermission]
    throttle_classes = [UserRateThrottle]

    @extend_schema(
        tags=["Shop"],
        request=GetBasketSerializer,
        responses={
            200: GetBasketSerializer(many=True),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Basket does not exist",
                examples=[
                    OpenApiExample(
                        "Basket not found",
                        value={"error": "You don't have an active basket"},
                        description="This error occurs when the "
                        "user does not have an active basket.",
                    )
                ],
            ),
            status.HTTP_401_UNAUTHORIZED: ErrorResponseSerializer,
        },
        methods=["GET"],
    )
    def get(self, request: Request) -> Response:
        """
        Handle GET request to retrieve items in user's basket.
        """
        try:
            basket_exists_validator(request.user)
            basket = Order.objects.filter(user=request.user, status="basket")
        except DRFValidationError as e:
            raise DRFValidationError({"error": e.args[0]})

        serializer = GetBasketSerializer(basket, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Shop"],
        responses={
            201: OpenApiResponse(
                response=SuccessResponseSerializer,
                description="Adding a product to basket",
                examples=[
                    OpenApiExample(
                        "Product added",
                        value={"message": "Product has been successfully added to basket"},
                        description="This example shows how to add a product to basket.",
                    )
                ],
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Validation errors during adding product to basket",
                examples=[
                    OpenApiExample(
                        "Basket not found",
                        value={"error": "You don't " "have an active basket"},
                        description="This error occurs when the "
                        "user does not have an active basket.",
                    ),
                    OpenApiExample(
                        "Incorrect data",
                        value={"error": "Incorrect request format"},
                        description="This error occurs when the "
                        "user passed incorrect format of the data.",
                    ),
                    OpenApiExample(
                        "Product_info or quantity are missing",
                        value={
                            "error": "Following parameters are required: product_info, quantity"
                        },
                        description="This error occurs when the "
                        "user didn't pass product_info or quantity values.",
                    ),
                ],
            ),
            status.HTTP_401_UNAUTHORIZED: ErrorResponseSerializer,
        },
        methods=["POST"],
    )
    def post(self, request: Request) -> Response:
        """
        Handle POST request to add items to user's basket.
        """
        items = request.data.get("items")

        try:
            json_data: List[Dict[str, int]] = json_validator(items)
        except DRFValidationError as e:
            raise DRFValidationError({"error": e.args[0]})

        if all([{"product_info", "quantity"}.issubset(elem.keys()) for elem in json_data]):
            try:
                product = ProductValidators(request_method=request.method, json_data=json_data)
                valid_products_dict = product.exist_validator()
                shop_ids: Set[int] = {product.shop_id for product in valid_products_dict.values()}
                shop_state_validator(shop_ids)
                valid_products_dict: Dict[int, ProductInfo] = product.quantity_validator()

            except DRFValidationError as e:
                raise DRFValidationError({"error": e.args[0]})

            order, _ = Order.objects.get_or_create(user=request.user, status="basket")

            try:
                already_ordered_products_validator(order, json_data)
            except DRFValidationError as e:
                raise DRFValidationError({"error": e.args[0]})

            with transaction.atomic():
                for index, elem in enumerate(json_data):
                    product_info_obj: ProductInfo = valid_products_dict.get(index)

                    OrderItem.objects.create(
                        order=order,
                        product=product_info_obj.product,
                        quantity=elem["quantity"],
                        shop=product_info_obj.shop,
                        product_info=product_info_obj,
                    )
            if len(valid_products_dict) == 1:
                return Response(
                    {"message": "Product has been successfully added to basket"},
                    status=status.HTTP_201_CREATED,
                )
            return Response(
                {"message": "Products have been successfully added to basket"},
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {"error": "Following parameters are required: product_info, quantity"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @extend_schema(
        tags=["Shop"],
        responses={
            200: OpenApiResponse(
                response=SuccessResponseSerializer,
                description="Basket updating",
                examples=[
                    OpenApiExample(
                        "Basket updated",
                        value={"message": "Basket has been successfully updated"},
                        description="This example shows how to update basket.",
                    )
                ],
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Validation errors during basket updating",
                examples=[
                    OpenApiExample(
                        "Basket not found",
                        value={"error": "You don't have an active basket"},
                        description="This error occurs when the "
                        "user does not have an active basket.",
                    ),
                    OpenApiExample(
                        "Incorrect data",
                        value={"error": "Incorrect request format"},
                        description="This error occurs when the "
                        "user passed incorrect format of the data.",
                    ),
                    OpenApiExample(
                        "Id or quantity are missing",
                        value={"error": "Following parameters are required: id, quantity"},
                        description="This error occurs when the "
                        "user didn't pass id or quantity values.",
                    ),
                ],
            ),
            status.HTTP_401_UNAUTHORIZED: ErrorResponseSerializer,
        },
        methods=["PATCH"],
    )
    def patch(self, request: Request) -> Response:
        """
        Handle PATCH request to update items in user's basket.
        """
        items: Optional[str] = request.data.get("items")

        try:
            json_data: List[Dict[str, int]] = json_validator(items)
        except DRFValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        if all([{"id", "quantity"}.issubset(elem.keys()) for elem in json_data]):
            try:
                basket: Order = basket_exists_validator(request.user)
            except DRFValidationError as e:
                raise DRFValidationError({"error": e.args[0]})

            try:
                product: ProductValidators = ProductValidators(
                    request_method=request.method, json_data=json_data, basket=basket
                )
                product.exist_validator()
                valid_products_dict = product.quantity_validator()

                with transaction.atomic():
                    for index, elem in enumerate(json_data):
                        order_item = valid_products_dict.get(index)
                        order_item.quantity = elem["quantity"]
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

    @extend_schema(
        tags=["Shop"],
        responses={
            204: OpenApiResponse(
                response=SuccessResponseSerializer,
                description="Product removing",
                examples=[
                    OpenApiExample(
                        "Product removed from basket",
                        value={"message": "Product has been successfully deleted from basket"},
                        description="This example shows how to remove product from basket.",
                    )
                ],
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Validation errors during products removing from basket",
                examples=[
                    OpenApiExample(
                        "Basket not found",
                        value={"error": "You don't have an active basket"},
                        description="This error occurs when the "
                        "user does not have an active basket.",
                    ),
                    OpenApiExample(
                        "Incorrect data",
                        value={"error": "Incorrect request format"},
                        description="This error occurs when the "
                        "user passed incorrect format of the data.",
                    ),
                    OpenApiExample(
                        "Product doesn't exist",
                        value={"error": "Product with {id} does not exist"},
                        description="This error occurs when the user is tring to "
                        "delete product that does not exist in the basket.",
                    ),
                ],
            ),
            status.HTTP_401_UNAUTHORIZED: ErrorResponseSerializer,
        },
        methods=["DELETE"],
    )
    def delete(self, request: Request) -> Response:
        """
        Handle DELETE request to remove items from user's basket.
        """
        items: Optional[str] = request.data.get("items")

        try:
            index_list: List[int] = list(map(int, items.split(",")))
        except ValueError:
            return Response(
                {"error": "Incorrect request format"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            basket: Order = Order.objects.get(user=request.user, status="basket")
        except Order.DoesNotExist:
            return Response(
                {"error": "You don't have active basket"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            product: ProductValidators = ProductValidators(
                request_method=request.method, basket=basket, index_list=index_list
            )
            valid_products_dict: Dict[int, OrderItem] = product.exist_validator()
        except DRFValidationError as e:
            raise DRFValidationError({"error": e.args[0]})

        indexes_to_delete: List[int] = list(valid_products_dict.keys())
        with transaction.atomic():
            order_items_to_delete: QuerySet[OrderItem] = OrderItem.objects.filter(
                id__in=indexes_to_delete
            )

            order_items_to_delete.delete()

        if len(valid_products_dict) == 1:
            return Response(
                {"message": "Product has been successfully deleted from basket"},
                status=status.HTTP_204_NO_CONTENT,
            )
        return Response(
            {"message": "Products have been successfully deleted from basket"},
            status=status.HTTP_204_NO_CONTENT,
        )


@extend_schema(
    tags=["Shop"],
    responses={
        200: OpenApiResponse(
            response=ShopSerializer,
            description="List of shops with pagination, filtering, search, and ordering",
        ),
    },
)
class ShopList(ListAPIView):
    """
    Class to list all shops with pagination, filtering, search, and ordering.
    """

    queryset = Shop.objects.all()
    serializer_class = ShopSerializer
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]
    pagination_class = PageNumberPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["name", "state"]
    search_fields = ["name", "state"]
    ordering_fields = ["name", "state"]
    ordering = ["name"]


@extend_schema(
    tags=["Shop"],
    responses={
        200: OpenApiResponse(
            response=CategorySerializer,
            description="List of categories with pagination, filtering, search, and ordering",
        ),
    },
)
class CategoryList(ListAPIView):
    """
    Class to list all categories with pagination, filtering, search, and ordering.
    """

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]
    pagination_class = PageNumberPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["id", "external_id", "name"]
    search_fields = ["id", "external_id", "name"]
    ordering_fields = ["id", "external_id", "name"]
    ordering = ["id"]


class TriggerError(APIView):

    permission_classes = [AllowAny]
    def get(self, request: Request) -> Response:
        return Response(data=(1 / 0), status=status.HTTP_500_INTERNAL_SERVER_ERROR)