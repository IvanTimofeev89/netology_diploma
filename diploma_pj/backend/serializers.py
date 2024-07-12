from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
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
        fields = ("name", "category", "product_info")

    def get_product_info(self, obj):
        product_info = ProductInfo.objects.filter(product=obj)
        return ProductInfoSerializer(product_info, many=True).data


class GetBasketSerializer(serializers.ModelSerializer):
    info = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ("id", "date", "status", "total", "info")
        read_only_fields = ("id",)

    def get_info(self, obj):
        if not hasattr(self, "_order_items"):
            self._order_items = OrderItem.objects.filter(order=obj).select_related(
                "product", "product_info"
            )

        serialized_items = []
        for item in self._order_items:
            serialized_items.append(
                {
                    "product_basket_id": item.id,
                    "name": item.product.name,
                    "price": item.product_info.price_rrc,
                    "quantity": item.quantity,
                }
            )
        return serialized_items

    def get_total(self, obj):
        if not hasattr(self, "_order_items"):
            self._order_items = OrderItem.objects.filter(order=obj).select_related("product_info")

        total = sum(item.quantity * item.product_info.price_rrc for item in self._order_items)
        return total
