from django.urls import path
from api.views import *

urlpatterns = [
    path('products/', ProductListView.as_view()),
    path('products/<int:pk>/', ProductDetailView.as_view()),
    path('search/', ProductSearchView.as_view(), name="productsearch"),
    path('add-to-cart/<int:pk>/', AddProductToCart.as_view()),
    # path('add-to-cart-detail/<int:pk>/', AddToCartDetail.as_view()),
    path('my-cart/', MyCartView.as_view()),
    path('manage-cart-items/<int:pk>/', ManageCartProductView.as_view()),
    path('empty-cart/', EmptyCartView.as_view()),
    path('checkout/', CheckOutView.as_view()),
    path("profile/", CustomerProfileView.as_view(), name="profile"),
    path("profile/order-<int:pk>/", CustomerOrderDetailView.as_view(),
         name="customerorderdetail"),


    # admin side
    # path("admin/login/", AdminLoginView.as_view(), name="adminlogin"),
    path("admin/orders/", AdminOrderListView.as_view(), name="adminorderlist"),
    path("admin/orders/<int:pk>/",
         AdminOrderDetailView.as_view(), name="adminorderdetail"),
    path("admin/orders-<int:pk>-change/",
         AdminOrderStatusChange.as_view(), name="adminorderstatuschange"),
    path('admin/products/', ProductListView.as_view()),
    path('admin/products/<int:pk>/', ProductDetailView.as_view()),
    path('admin/products/add/', AdminAddProductView.as_view(), name="addproduct"),
]
