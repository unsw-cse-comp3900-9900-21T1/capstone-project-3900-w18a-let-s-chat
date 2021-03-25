from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms

from .models import Order, Customer, Product

class OrderForm(ModelForm):
    class Meta:
        model = Order
        fields = '__all__'

class CreateUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class UpdateUserForm(ModelForm):
    class Meta:
        model = Customer
        fields = ['nickname', 'email', 'contactNo']

class UpdateUserProfilePic(ModelForm):
    class Meta:
        model = Customer
        fields = ['image']

class CreateProductForm(ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'price', 'description', 'isAnimal', 'warranty', 'delivery_period', 'remaining_unit', 'image', 'tags']
        labels = {
            'isAnimal': 'Animal?',
            'remaining_unit': 'Units available',
            'image': 'Choose an image for your listing'
        }
     
    def __init__(self, *args, **kwargs):
        super(CreateProductForm, self).__init__(*args, **kwargs)
        #self.fields['image'].required = True

class EditProductForm(ModelForm):

    clear_existing_tags = forms.BooleanField(initial=False)

    class Meta:
        model = Product
        fields = ['name', 'price', 'remaining_unit', 'description', 'tags']
        labels = {
            'remaining_unit': 'Units available',
            'image': 'Change product image'
        }
    def __init__(self, *args, **kwargs):
        super(EditProductForm, self).__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].required = False