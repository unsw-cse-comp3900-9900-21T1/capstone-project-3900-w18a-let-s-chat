from django.shortcuts import render
from .models import *
from django.contrib.auth.forms import UserCreationForm

# Create your views here.
from .forms import OrderForm, CreateUserForm

def store(request):
	products = Product.objects.all()
	context = {'products':products}
	return render(request, 'store/store.html', context)

def signup(request):
	form = CreateUserForm()

	if request.method == "POST":
		form = CreateUserForm(request.POST)
		if form.is_valid():
			form.save()
	
	context = {'form':form}
	return render(request, 'store/signup.html', context)

def login(request):
	context = {}
	return render(request, 'store/login.html', context)

def product_description(request):
	context = {}
	return render(request, 'store/product_description.html', context)

def cart(request):

	if request.user.is_authenticated:
		customer = request.user.customer
		order, created = Order.objects.get_or_create(customer=customer, complete=False)
		items = order.orderitem_set.all()
	else:
		#Create empty cart for now for non-logged in user
		items = []
		order = {'get_cart_total':0, 'get_cart_items':0}

	context = {'items':items, 'order':order}
	return render(request, 'store/cart.html', context)

def checkout(request):
	if request.user.is_authenticated:
		customer = request.user.customer
		order, created = Order.objects.get_or_create(customer=customer, complete=False)
		items = order.orderitem_set.all()
	else:
		#Create empty cart for now for non-logged in user
		items = []
		order = {'get_cart_total':0, 'get_cart_items':0}

	context = {'items':items, 'order':order}
	return render(request, 'store/checkout.html', context)

def purchase_history(request):
	context = {}
	return render(request, 'store/purchase_history.html', context)

def wishList(request):
	context = {}
	return render(request, 'store/wishList.html', context)

# watchlist is a list of auction items that user watch to see
def watchList(request):
	context = {}
	return render(request, 'store/watchList.html', context)