from django.urls import path
from .views import *

app_name = "ecomapp"
urlpatterns = [
    # customer side
    path('', HomeView.as_view(), name="home"),
    path('about/', AboutView.as_view(), name="about"),
    path('contact-us/', ContactView.as_view(), name="contact"),
    path('all-products/', AllProdutView.as_view(), name="all-products"),
    path("product/<slug:slug>/", ProductDetailView.as_view(), name="product-detail"),
    path("search/", SearchView.as_view(), name="search"),
    path("add-to-cart/<int:pro_id>/", AddToCartView.as_view(), name="add-to-cart"),
    path("my-cart/", MyCartView.as_view(), name="my-cart"),
    path("manage-cart/<int:cp_id>/", ManageCartView.as_view(), name="managecart"),
    path("empty-cart/", EmptyCartView.as_view(), name="empty-cart"),

    path("checkout/", CheckOutView.as_view(), name="checkout"),
    path("esewa-verify/", EsewaVerifyView.as_view(), name="esewaverify"),

    path("register/", CustomerRegistrationView.as_view(), name="register"),
    path("logout/", CustomerLogoutView.as_view(), name="logout"),
    path("login/", CustomerLoginView.as_view(), name="login"),
    path("profile/", CustomerProfileView.as_view(),
         name="profile"),
    path("profile/order-<int:pk>/", CustomerOrderDetailView.as_view(),
         name="customer-order-detail"),
    path("forgot-password/", ForgotPasswordView.as_view(), name="forgotpassword"),

    # admin side
    path("admin-login/", AdminLoginView.as_view(), name="adminlogin"),
    path("admin-home/", AdminHome.as_view(), name="adminhome"),
    path("admin-order/<int:pk>/", AdminOrderDetailView.as_view(), name="adminorder"),
    path("admin-all-orders/", AdminOrderListView.as_view(), name="adminorderlist"),
    path("admin-order-<int:pk>-change/",
         AdminOrderStatusChangeView.as_view(), name="adminorderstatuschange"),

    path("admin-product/list/", AdminProductListView.as_view(),
         name="adminproductlist"),
    path("admin-product/add/", AdminProductCreateView.as_view(),
         name="adminproductadd"),

    # payment
    path("esewa-request/", EsewaRequestView.as_view(), name="esewarequest"),
]
