from django import forms
from .models import Customer, Order, Product
from django.contrib.auth.models import User


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['ordered_by', 'shipping_address',
                  'mobile', 'email', 'payment_method']


class CustomerRegistrationForm(forms.ModelForm):
    username = forms.CharField(widget=forms.TextInput())
    password = forms.CharField(widget=forms.PasswordInput())
    email = forms.CharField(widget=forms.EmailInput())

    class Meta:
        model = Customer
        fields = ["full_name", "address"]

    # checking or validating if user already exists while registering
    def clean_username(self):
        username = self.cleaned_data.get("username")
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(
                'Customer with username already exists.')
        return username


class CustomerLoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput())
    password = forms.CharField(widget=forms.PasswordInput())

#  clearable file input vs fileinput
#  clearble file input is used in update view to show the previously
#  uploaded image and  there is a feature to remove that image
#  but fileinput does not allow us


class ProductForm(forms.ModelForm):
    # custom field is not saved in the database by createview so
    # mechanism to catch that is needed.
    more_images = forms.FileField(required=False, widget=forms.FileInput(attrs={
        "class": "form-control",
        "multiple": True
    }))

    class Meta:
        model = Product
        fields = ["title", "slug", "category", "image", "marked_price",
                  "selling_price", "description", "warranty", "return_policy"]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter the product title here..."
            }),
            "slug": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter the unique slug here..."
            }),
            "category": forms.Select(attrs={
                "class": "form-control"
            }),
            "image": forms.ClearableFileInput(attrs={
                "class": "form-control"
            }),
            "marked_price": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Marked price of the product..."
            }),
            "selling_price": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Selling price of the product..."
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "placeholder": "Description of the product...",
                "rows": 5
            }),
            "warranty": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter the product warranty here..."
            }),
            "return_policy": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter the product return policy here..."
            }),
        }


class PasswordResetForm(forms.Form):
    email = forms.CharField(widget=forms.EmailInput(attrs={
        "class": "form-control",
        "placeholder": "Enter your email to find account."
    }))

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if Customer.objects.filter(user__email=email).exists():
            pass
        else:
            raise forms.ValidationError(
                "Customer with this account does not exists...")
        return email
