from cmath import log
from itertools import product
from math import prod
from multiprocessing import context
from pipes import Template
from urllib import request
from django.shortcuts import render, redirect
from django.views.generic import View, TemplateView, CreateView, FormView, DetailView, ListView
from .forms import *
from .models import *
from django.urls import reverse_lazy, reverse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q
from django.core.paginator import Paginator

from .utils import password_reset_token
from django.core.mail import send_mail
from django.conf import settings


class EcomMixin(object):
    def dispatch(self, request, *args, **kwargs):
        cart_id = request.session.get("cart_id")
        if cart_id:
            cart_obj = Cart.objects.get(id=cart_id)
            if request.user.is_authenticated and request.user.customer:
                # assigning customer to a cart object
                cart_obj.customer = request.user.customer
                cart_obj.save()
        return super().dispatch(request, *args, **kwargs)


class HomeView(EcomMixin, TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        allproducts = Product.objects.all().order_by("-id")

        # pagination
        paginator = Paginator(allproducts, 4)
        page_number = self.request.GET.get('page')
        product_list = paginator.get_page(page_number)
        context['product_list'] = product_list
        return context


class AllProdutView(EcomMixin, TemplateView):
    template_name = 'allproducts.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['allcategories'] = Category.objects.all()
        return context


class ProductDetailView(EcomMixin, TemplateView):
    template_name = "product_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        url_slug = self.kwargs['slug']
        product = Product.objects.get(slug=url_slug)
        product.view_count += 1
        product.save()
        context['product'] = product
        return context


# search functionality


class SearchView(TemplateView):
    template_name = "search.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        keyword = self.request.GET["keyword"]
        pro_obj = Product.objects.filter(
            Q(title__icontains=keyword) | Q(description__icontains=keyword))
        context['product_list'] = pro_obj
        return context


class AddToCartView(EcomMixin, TemplateView):
    template_name = "add_to_cart.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # get product id from requested url
        product_id = self.kwargs['pro_id']

        # get product
        product_obj = Product.objects.get(id=product_id)

        # check if cart exits and if exits, creating session id
        # for cart_id identification
        # return none if session id not found
        cart_id = self.request.session.get('cart_id', None)
        print(cart_id, "id")

        if cart_id:
            cart_obj = Cart.objects.get(id=cart_id)
            print('old cart')

            this_product_in_cart = cart_obj.cartproducts.filter(
                product=product_obj)
            print("Already exited product:", this_product_in_cart)

            # item already exists in cart
            if this_product_in_cart.exists():
                cartproduct = this_product_in_cart.first()
                cartproduct.quantity += 1
                cartproduct.subtotal += product_obj.selling_price
                cartproduct.save()
                cart_obj.total += product_obj.selling_price
                cart_obj.save()

            # new item exitst in cart
            else:
                cartproduct = CartProduct.objects.create(
                    cart=cart_obj, product=product_obj, rate=product_obj.selling_price, quantity=1, subtotal=product_obj.selling_price)
                cart_obj.total += product_obj.selling_price
                cart_obj.save()

        else:
            cart_obj = Cart.objects.create(total=0)
            print(cart_obj, 'newly created*********')
            self.request.session['cart_id'] = cart_obj.id

            cartproduct = CartProduct.objects.create(
                cart=cart_obj, product=product_obj, rate=product_obj.selling_price, quantity=1, subtotal=product_obj.selling_price)
            cartproduct.save()
            cart_obj.total += product_obj.selling_price
            cart_obj.save()

        # check if product already exists in cart
        return context


class MyCartView(EcomMixin, TemplateView):
    template_name = "my_cart.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # checking if cart already exists in the session
        cart_id = self.request.session.get("cart_id", None)
        if cart_id:
            cart = Cart.objects.get(id=cart_id)
        else:
            cart = None
        context['cart'] = cart
        return context


class ManageCartView(EcomMixin, View):
    def get(self, request, *args, **kwargs):
        cp_id = self.kwargs["cp_id"]
        cp_obj = CartProduct.objects.get(id=cp_id)
        cart_obj = cp_obj.cart

        action = request.GET.get("action")
        print(cp_id, action)

        if action == "inc":
            cp_obj.quantity += 1
            cp_obj.subtotal += cp_obj.rate
            cp_obj.save()
            cart_obj.total += cp_obj.rate
            cart_obj.save()
        elif action == "dec":
            cp_obj.quantity -= 1
            cp_obj.subtotal -= cp_obj.rate
            cp_obj.save()
            cart_obj.total -= cp_obj.rate
            cart_obj.save()
            if cp_obj.quantity == 0:
                cp_obj.delete()
        elif action == "rmv":
            cart_obj.total -= cp_obj.subtotal
            cart_obj.save()
            cp_obj.delete()
        return redirect("ecomapp:my-cart")


class EmptyCartView(EcomMixin, View):
    def get(self, request, *args, **kwargs):
        cart_id = request.session.get("cart_id", None)
        if cart_id:
            cart = Cart.objects.get(id=cart_id)
            cart.cartproducts.all().delete()
            cart.total = 0
            cart.save()
        return redirect("ecomapp:my-cart")


class CheckOutView(EcomMixin, CreateView):
    template_name = "checkout.html"
    # render form in template
    form_class = CheckoutForm
    success_url = reverse_lazy("ecomapp:home")

    # dispatch method -> runs before other method
    # check whether the user is logged in and user is customer or not
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.customer:
            print("Logged in user")
        else:
            # when
            return redirect("/login/?next=/checkout/")

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart_id = self.request.session.get("cart_id", None)
        if cart_id:
            cart_obj = Cart.objects.get(id=cart_id)
        else:
            cart_obj = None
        context['cart'] = cart_obj
        return context

    # handling incomplete form fields
    def form_valid(self, form):
        cart_id = self.request.session.get("cart_id")
        if cart_id:
            cart_obj = Cart.objects.get(id=cart_id)
            form.instance.cart = cart_obj
            form.instance.subtotal = cart_obj.total
            form.instance.discount = 0
            form.instance.total = cart_obj.total
            form.instance.order_status = "Order Received"
            del self.request.session['cart_id']

            pm = form.cleaned_data['payment_method']
            order = form.save()
            print("-----before error---")
            if pm == "Esewa":
                return redirect(reverse("ecomapp:esewarequest") + "?o_id=" + str(order.id))
        else:
            return redirect("ecomapp:home")
        return super().form_valid(form)


class CustomerRegistrationView(CreateView):
    template_name = "register.html"
    form_class = CustomerRegistrationForm
    success_url = reverse_lazy("ecomapp:home")

# or we can also use post method
    def form_valid(self, form):
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        email = form.cleaned_data.get('email')
        user_obj = User.objects.create_user(username, email, password)
        form.instance.user = user_obj
        login(self.request, user_obj)
        return super().form_valid(form)

        # if next is found in url, redirect user to checkout
    def get_success_url(self):
        if "next" in self.request.GET:
            next_url = self.request.GET.get("next")
            # we don't have to redirect here 'cause it is
            # get_sucess_url method, we just have to provide url pattern
            # which automatically gets redirected
            return next_url
        else:
            return self.success_url


class CustomerLogoutView(View):
    def get(self, request):
        logout(request)
        return redirect("ecomapp:home")


class CustomerLoginView(FormView):
    template_name = "login.html"
    form_class = CustomerLoginForm
    success_url = reverse_lazy("ecomapp:home")

    # form valid is a post method and is available in CreateView, FormView and UpdateView
    # self is the attribute of the same class
    def form_valid(self, form):
        # another method of getting dict data
        username = form.cleaned_data["username"]
        password = form.cleaned_data["password"]
        # if credential does not match, it returns None
        user = authenticate(username=username, password=password)
        if user is not None and Customer.objects.filter(user=user).exists():
            login(self.request, user)
        else:
            return render(self.request, self.template_name, {"form": self.form_class, "error": "Invalid credentitals"})
        return super().form_valid(form)

    # if next is found in url, redirect user to checkout
    def get_success_url(self):
        if "next" in self.request.GET:
            next_url = self.request.GET.get("next")
            # we don't have to redirect here 'cause it is
            # get_sucess_url method, we just have to provide url pattern
            # which automatically gets redirected
            return next_url
        else:
            return self.success_url


class AboutView(EcomMixin, TemplateView):
    template_name = "about.html"


class ContactView(EcomMixin, TemplateView):
    template_name = "contactus.html"


class CustomerProfileView(TemplateView):
    template_name = 'customerprofile.html'

    def dispatch(self, request, *args, **kwargs):
        # redirect user to login if not authenticated and then to profile
        if request.user.is_authenticated and Customer.objects.filter(user=request.user).exists():
            pass
        else:
            # when
            return redirect("/login/?next=/profile/")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer = self.request.user.customer
        context["customer"] = customer
        orders = Order.objects.filter(cart__customer=customer).order_by("-id")
        context["orders"] = orders
        return context


class CustomerOrderDetailView(DetailView):
    template_name = 'customerorderdetail.html'
    model = Order

    # context_object_name = "ord_obj" -> does not work here why?

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and Customer.objects.filter(user=request.user).exists():
            order_id = self.kwargs['pk']
            # checking order avaliability i.e. from url product id
            try:
                order = Order.objects.get(id=order_id)
            except Order.DoesNotExist:
                print("does not exist to your account")
                return redirect('ecomapp:profile')
            else:
                # redirect user if the order are not made by him
                if request.user.customer != order.cart.customer:
                    return redirect('ecomapp:profile')
        else:
            # when
            return redirect("/login/?next=/profile/")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ord_id = self.kwargs["pk"]
        ord_obj = Order.objects.get(id=ord_id)
        context["ord_obj"] = ord_obj
        return context

# admin page


# redirect user to login if not authenticated and then to profile
class AdminRequiredMixin(object):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and Admin.objects.filter(user=request.user).exists():
            pass
        else:
            return redirect("adminlogin")
        return super().dispatch(request, *args, **kwargs)


class AdminLoginView(AdminRequiredMixin, FormView):
    template_name = "adminpages/adminlogin.html"
    form_class = CustomerLoginForm
    success_url = reverse_lazy('ecomapp:adminhome')

    def form_valid(self, form):
        # another method of getting dict data
        username = form.cleaned_data["username"]
        password = form.cleaned_data["password"]
        # if credential does not match, it returns None
        user = authenticate(username=username, password=password)
        if user is not None and Admin.objects.filter(user=user).exists():
            login(self.request, user)
        else:
            return render(self.request, self.template_name, {"form": self.form_class, "error": "Invalid credentitals"})
        return super().form_valid(form)


class AdminHome(AdminRequiredMixin, TemplateView):
    template_name = "adminpages/adminhome.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pendingorders"] = Order.objects.filter(
            order_status="Order Received"
        ).order_by("-id")
        return context


class AdminOrderDetailView(AdminRequiredMixin, DetailView):
    template_name = "adminpages/adminorderdetail.html"
    model = Order
    context_object_name = 'ord_obj'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['allstatus'] = ORDER_STATUS
        return context


class AdminOrderListView(AdminRequiredMixin, ListView):
    template_name = "adminpages/admin_order_list.html"
    queryset = Order.objects.all().order_by("-id")
    context_object_name = "all_orders"


class AdminOrderStatusChangeView(AdminRequiredMixin, View):
    def post(self, request, *args, **kwrgs):
        order_id = self.kwargs['pk']
        order_obj = Order.objects.get(id=order_id)
        # get changed status
        new_status = request.POST.get("status")
        order_obj.order_status = new_status
        order_obj.save()
        return redirect(reverse_lazy('ecomapp:adminorder', kwargs={"pk": order_id}))


class AdminProductListView(AdminRequiredMixin, ListView):
    template_name = "adminpages/adminproductlist.html"
    queryset = Product.objects.all().order_by("-id")
    context_object_name = "allproducts"


class AdminProductCreateView(AdminRequiredMixin, CreateView):
    template_name = "adminpages/adminproductadd.html"
    form_class = ProductForm
    success_url = reverse_lazy('ecomapp:adminproductadd')

# only needed to handle more_images field
    def form_valid(self, form):
        product = form.save()
        print("product----->", product)
        images = self.request.FILES.getlist("more_images")
        for i in images:
            ProductImage.objects.create(product=product, image=i)
        return super().form_valid(form)


class ForgotPasswordView(FormView):
    template_name = "forgotpassword.html"
    form_class = PasswordResetForm
    success_url = "/forgot-password/"

    def form_valid(self, form):
        email = form.cleaned_data.get("email")
        url = self.request.META['HTTP_HOST']
        customer = Customer.objects.get(user__email=email)
        user = customer.user
        print("---url---", url)
        text_content = 'Please Click the link below to reset your password.'
        html_content = url + "/password-reset/" + email + \
            "/" + password_reset_token.make_token(user) + "/"
        send_mail(
            'Password Reset Link | Django Ecommerce',
            text_content + html_content,
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )
        return super().form_valid(form)

# payment view


class EsewaRequestView(View):
    def get(self, request, *args, **kwargs):
        o_id = request.GET.get("o_id")
        order = Order.objects.get(id=o_id)
        context = {
            "order": order
        }
        return render(request, 'esewarequest.html', context)
