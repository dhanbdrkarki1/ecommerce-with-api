from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api.serializers import *
from django.db.models import Q
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from api.customauth import *
from api.permissions import IsAdminUser, IsCustomerUser


class ProductListView(APIView):
    def get(self, request):
        product = Product.objects.all()
        serializer = ProductSerializer(product, many=True)
        return Response(serializer.data)


class ProductDetailView(APIView):
    def get_object(self, pk):
        try:
            product = Product.objects.get(pk=pk)
            product.view_count += 1
            product.save()
            return product
        except Product.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        product = self.get_object(pk)

        serializer = ProductSerializer(product)
        return Response(serializer.data)

    def put(self, request, pk):
        product = self.get_object(pk)
        serializer = ProductSerializer(product, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        product = self.get_object(pk)
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductSearchView(APIView):
    def get(self, request):
        keyword = request.GET["keyword"]
        pro_obj = Product.objects.filter(
            Q(title__icontains=keyword) | Q(description__icontains=keyword))
        if pro_obj.count() == 0:
            msg = "No search results found"
        else:
            msg = "Search results:"
        serializer = ProductSerializer(pro_obj, many=True)
        data = {
            'msg': msg,
            'products': serializer.data
        }
        return Response(data, status=status.HTTP_200_OK)


class AddProductToCart(APIView):
    def get(self, request, pk):
        product_obj = Product.objects.get(pk=pk)
        print(product_obj)

        cart_id = self.request.session.get('cart_id', None)
        if cart_id:
            cart_obj = Cart.objects.get(id=cart_id)
            this_product_in_cart = cart_obj.cartproducts.filter(
                product=product_obj)
            print("Already exists-----", this_product_in_cart)

            if not this_product_in_cart.exists():
                cartproduct = CartProduct.objects.create(cart=cart_obj, product=product_obj,
                                                         rate=product_obj.selling_price, quantity=1,
                                                         subtotal=product_obj.selling_price
                                                         )
                cart_obj.total += product_obj.selling_price
                cart_obj.save()
                print("item exists in cart --------")

            else:
                cartproduct = this_product_in_cart.first()
                cartproduct.quantity += 1
                cartproduct.subtotal += product_obj.selling_price
                cartproduct.save()
                cart_obj.total += product_obj.selling_price
                cart_obj.save()
                print("items already exists in cart-------")

        else:
            cart_obj = Cart.objects.create(total=0)
            print(cart_obj, 'newly created*********')
            self.request.session['cart_id'] = cart_obj.id
            cartproduct = CartProduct.objects.create(
                cart=cart_obj, product=product_obj, rate=product_obj.selling_price,
                quantity=1, subtotal=product_obj.selling_price)
            cartproduct.save()
            cart_obj.total += product_obj.selling_price
            cart_obj.save()
        serializer = CartSerializer(cart_obj)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MyCartView(APIView):
    def get(self, request):
        cart_id = self.request.session.get("cart_id", None)
        if cart_id:
            cart = Cart.objects.get(id=cart_id)
            serializer = CartSerializer(cart)
            return Response(serializer.data)
        else:
            cart = None
        return Response("Cart Not Available")


class ManageCartProductView(APIView):
    def get(self, request, pk):
        cp_obj = CartProduct.objects.get(id=pk)
        cart_obj = cp_obj.cart

        action = request.GET.get("action")
        print("-------action--", action)
        message = ''

        if action == "inc":
            cp_obj.quantity += 1
            cp_obj.subtotal += cp_obj.rate
            cp_obj.save()
            cart_obj.total += cp_obj.rate
            cart_obj.save()
            message = "Product Quantity Added..."

        elif (action == "dec"):
            if cp_obj.quantity != 0:
                cp_obj.quantity -= 1
                cp_obj.subtotal -= cp_obj.rate
                cp_obj.save()
                cart_obj.total -= cp_obj.rate
                cart_obj.save()
                message = "Product Quantity decreased..."
            else:
                cp_obj.delete()
                message = "product removed....."
        elif (action == "del"):
            cart_obj.total -= cp_obj.subtotal
            cart_obj.save()
            cp_obj.delete()
            message = "Product removed"
        serializer = CartProductSerializer(cp_obj)
        data = {
            'products': serializer.data,
            'message': message
        }
        return Response(data, status=status.HTTP_200_OK)


class EmptyCartView(APIView):
    def get(self, request):
        cart_id = request.session.get("cart_id", None)
        print("---------", cart_id)
        if cart_id:
            cart = Cart.objects.get(id=cart_id)
            cart.cartproducts.all().delete()
            cart.total = 0
            cart.save()
        return Response("Cart deleted....", status=status.HTTP_204_NO_CONTENT)


class CheckOutView(APIView):
    authentication_classes = [BasicAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated, IsCustomerUser]

    def get(self, request):
        cart_id = self.request.session.get("cart_id", None)
        if cart_id:
            cart_obj = Cart.objects.filter(id=cart_id).first()
            cart_obj.customer = request.user.customer
            order_obj = Order.objects.create(cart=cart_obj,
                                             ordered_by="Hima Karki", shipping_address="Jhapa",
                                             mobile="988787877", email="me.ankita@gmail.com",
                                             subtotal=cart_obj.total, discount=0,
                                             total=cart_obj.total, order_status="Order Received", payment_completed=True)
            print("Order--------", order_obj)
            del self.request.session["cart_id"]
            serializer = OrderSerializer(order_obj)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            msg = "No item in cart added to place order..."
        return Response(msg, status=status.HTTP_204_NO_CONTENT)


class CustomerProfileView(APIView):
    authentication_classes = [BasicAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated, IsCustomerUser]

    def get(self, request):
        customer = self.request.user.customer
        orders = Order.objects.filter(
            cart__customer=customer).order_by("-id")
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CustomerOrderDetailView(APIView):
    authentication_classes = [BasicAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated, IsCustomerUser]

    def get_object(self, pk):
        try:
            order = Order.objects.get(pk=pk)
            return order
        except Order.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        order_obj = self.get_object(pk)
        serializer = OrderSerializer(order_obj)
        return Response(serializer.data, status=status.HTTP_200_OK)


# admin
class AdminOrderListView(APIView):
    authentication_classes = [BasicAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        orders = Order.objects.all()
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminOrderDetailView(APIView):
    authentication_classes = [BasicAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, pk):
        orders = Order.objects.get(id=pk)
        serializer = OrderSerializer(orders)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminOrderStatusChange(APIView):
    authentication_classes = [BasicAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUser]

    def put(self, request, pk):
        order_obj = Order.objects.get(id=pk)
        new_status = request.POST.get("status")
        order_obj.order_status = new_status
        order_obj.save()
        serializers = OrderSerializer(order_obj)
        return Response(serializers.data, status=status.HTTP_202_ACCEPTED)


class AdminAddProductView(APIView):
    authentication_classes = [BasicAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
