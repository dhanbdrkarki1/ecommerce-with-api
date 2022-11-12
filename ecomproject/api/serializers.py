from rest_framework import serializers
from ecomapp.models import *


class CustomerSerializers(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['user', 'full_name', 'address']


class CategorySerializers(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'title', 'slug']


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'title', 'slug', 'category', 'image', 'marked_price',
                  'selling_price', 'description', 'warranty', 'return_policy', 'view_count']


class CartProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartProduct
        fields = ['id', 'product', 'rate', 'quantity', 'subtotal']
        # depth = 1


class CartSerializer(serializers.ModelSerializer):
    cartproducts = CartProductSerializer(many=True)

    class Meta:
        model = Cart
        fields = ['id', 'customer', 'total', 'cartproducts']

    def create(self, validated_data):
        cartproducts_data = validated_data.pop('cartproducts')
        cart = Cart.objects.create(**validated_data)
        for cpd in cartproducts_data:
            CartProduct.objects.create(cart=cart, **cpd)
        return cart


class OrderSerializer(serializers.ModelSerializer):
    cart = CartSerializer()

    class Meta:
        model = Order
        fields = ['id', 'ordered_by', 'shipping_address', 'mobile',
                  'email', 'order_status', 'payment_method', 'payment_completed', 'cart']


class AdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Admin
