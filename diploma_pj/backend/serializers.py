from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db.models import Q
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
        fields = ("email", "first_name", "last_name", "middle_name", "company", "position")

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
        fields = ("email", "first_name", "last_name", "middle_name", "company", "position", "type")
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
        fields = ("id", "quantity", "price_rrc", "shop")

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
        order_items = OrderItem.objects.filter(order=obj)

        # Создаем словарь для хранения уникальных пар product_id и shop_id
        unique_pairs = {}
        for item in order_items:
            unique_pairs[
                (item.product_id, item.shop_id)
            ] = None  # Используем None в качестве значения, которое мы затем заменим на ProductInfo

        # Создаем список Q-объектов для фильтрации ProductInfo
        q_objects = Q()
        for product_id, shop_id in unique_pairs.keys():
            q_objects |= Q(product_id=product_id, shop_id=shop_id)

        product_info_objs = list(ProductInfo.objects.filter(q_objects))

        # Теперь заполняем словарь unique_pairs сами объектами ProductInfo
        for product_info in product_info_objs:
            unique_pairs[(product_info.product_id, product_info.shop_id)] = product_info

        # Теперь заполняем список serialized_items
        serialized_items = []
        for item in order_items:
            product_info = unique_pairs[(item.product_id, item.shop_id)]
            serialized_items.append(
                {
                    "id": item.id,
                    "name": product_info.product.name,
                    "price": product_info.price_rrc,
                    "quantity": item.quantity,
                }
            )

        return serialized_items
