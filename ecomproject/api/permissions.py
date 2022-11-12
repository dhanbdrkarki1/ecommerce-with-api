from rest_framework import permissions
from ecomapp.models import Admin, Customer


class IsAdminUser(permissions.BasePermission):
    message = "You are not authorized bla bla"

    def has_permission(self, request, view):
        if request.user.is_authenticated and Admin.objects.filter(user=request.user).exists():
            return True


class IsCustomerUser(permissions.BasePermission):
    message = "You are not authorized."

    def has_permission(self, request, view):
        if request.user.is_authenticated and Customer.objects.filter(user=request.user).exists():
            return True
