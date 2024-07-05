from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db.models import F, Q
from rest_framework import serializers

from .models import (
    Category,
    Contact,
    Order,
    OrderItem,
    Product,
    ProductInfo,
    Shop,
    User,
)


class RegisterUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "middle_name", "company", "position", "type")

    def validate(self, data):
        password = self.initial_data.get("password")
        email = self.initial_data.get("email")

        if not password:
            raise serializers.ValidationError("Password is required")
        if not email:
            raise serializers.ValidationError("Email is required")
        try:
            validated_password = validate_password(password)
        except ValidationError as error:
            raise serializers.ValidationError({"password": error})
        data["password"] = validated_password
        return data

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = (
            "id",
            "city",
            "street",
            "house",
            "structure",
            "building",
            "apartment",
            "phone",
            "user",
        )
        read_only_fields = ("id",)
        extra_kwargs = {"user": {"write_only": True}}


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "middle_name", "company", "position")
        read_only_fields = ("email",)


class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ("id", "name", "url", "state")
        read_only_fields = ("id",)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "external_id", "name")
        read_only_fields = ("id",)


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ("id", "date", "status", "user")
        read_only_fields = ("id",)


class ProductInfoSerializer(serializers.ModelSerializer):
    shop = serializers.SerializerMethodField()

    class Meta:
        model = ProductInfo
        fields = ("quantity", "price_rrc", "shop")

    def get_shop(self, obj):
        shop = Shop.objects.get(id=obj.shop_id)
        return {"shop_id": shop.id, "shop_name": shop.name}


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    product_info = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ("id", "name", "category", "product_info")

    def get_product_info(self, obj):
        product_info = ProductInfo.objects.filter(product=obj)
        return ProductInfoSerializer(product_info, many=True).data

class GetBasketSerializer(serializers.ModelSerializer):
    info = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ("id", "date", "status", "info")
        read_only_fields = ("id",)

    def get_info(self, obj):
        # Получаем все OrderItem для данного заказа (obj)
        order_items = OrderItem.objects.filter(order=obj)

        # Собираем все id продуктов и магазинов для оптимизации запроса
        product_ids = [item.product_id for item in order_items]
        shop_ids = [item.shop_id for item in order_items]

        # Собираем Q-объекты для фильтрации ProductInfo
        q_objects = Q()
        for product_id, shop_id in zip(product_ids, shop_ids):
            q_objects |= Q(product_id=product_id, shop_id=shop_id)

        # Выполняем запрос к ProductInfo с использованием q_objects
        product_infos = ProductInfo.objects.filter(q_objects)

        # Сериализуем результат
        serialized_items = []
        for item, product_info in zip(order_items, product_infos):
            serialized_items.append({
                "name": product_info.product.name,
                "price": product_info.price_rrc,
                "quantity": item.quantity,
            })

# class GetBasketSerializer(serializers.ModelSerializer):
#     info = serializers.SerializerMethodField()
#
#     class Meta:
#         model = Order
#         fields = ("id", "date", "status", "info")
#         read_only_fields = ("id",)
#
#     def get_info(self, obj):
#         order_items = OrderItem.objects.filter(order=obj)
#
#         serialized_items = []
#         for item in order_items:
#             product_info = ProductInfo.objects.get(product=item.product, shop=item.shop)
#             serialized_items.append(
#                 {
#                     "name": product_info.product.name,
#                     "price": product_info.price_rrc,
#                     "quantity": item.quantity,
#                 }
#             )
#
#         return serialized_items
