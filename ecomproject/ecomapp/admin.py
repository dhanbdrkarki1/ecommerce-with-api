from django.contrib import admin
from .models import *

admin.site.register([Customer, Category, Product, ProductImage,
                    Cart, CartProduct, Order, Admin])
