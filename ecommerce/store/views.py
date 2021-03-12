from django.shortcuts import render, redirect, reverse
from .models import *
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.core.mail import EmailMessage
from django.conf import settings
from django.template.loader import render_to_string

# Create your views here.
from .forms import OrderForm, CreateUserForm, UpdateUserForm, UpdateUserProfilePic

def store(request):
	products = Product.objects.all()
	context = {'products':products}
	return render(request, 'store/store.html', context)

def signup(request):
	if request.user.is_authenticated:
		return redirect('store')
	else:
		form = CreateUserForm()
		if request.method == "POST":
			form = CreateUserForm(request.POST)
			if form.is_valid():
				user = form.save()
				username = form.cleaned_data.get('username')

				#messages.success(request, 'Account was created for ' + username)

				# create customer here
				customer = Customer()
				customer.user = user
				customer.nickname = user.username
				customer.email = user.email
				customer.save()

				template = render_to_string('store/email_template.html', {'name': user.username, 'username': user.username})

				print(settings.EMAIL_HOST_USER)
				email = EmailMessage(
					'You have successfully signed up for Petiverse!',
					template,
					settings.EMAIL_HOST_USER,
					[user.email],
				)

				email.fail_silently = False
				email.send()

				return redirect('signup_success')
				# username = user.username
				# email = user.email
				# Somehow it just cannot redirect to it when it has parameters
				# return redirect('signup_success', username, email)
	
	context = {'form':form}
	return render(request, 'store/signup.html', context)

def signup_success(request):
	# template = render_to_string('store/email_template.html', {'name': username, 'username': username})

	# print(settings.EMAIL_HOST_USER)
	# email = EmailMessage(
	# 	'You have successfully signed up for Petiverse!',
	# 	template,
	# 	settings.EMAIL_HOST_USER,
	# 	[email],
	# )

	# email.fail_silently = False
	# email.send()

	context = {}
	return render(request, 'store/signup_success.html', context)

def loginPage(request):
	if request.user.is_authenticated:
		return redirect('store')
	else:
		if request.method == 'POST':
			username = request.POST.get('username')
			password = request.POST.get('password')
			user = authenticate(request, username=username, password=password)

			if user is not None:
				login(request, user)
				return redirect('store')
			else:
				messages.info(request, 'Username OR password is incorrect')

	context = {}
	return render(request, 'store/login.html', context)

def logoutUser(request):
	logout(request)
	return redirect('login')

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
	if not request.user.is_authenticated:
		return redirect('login')

	customer = request.user.customer
	orders = Order.objects.filter(customer=customer)
	order_items = OrderItem.objects.filter(order__in=orders).order_by('-date_added')

	purchases = []
	for item in order_items:
		purchases.append({
			"name": item.product.name,
			"seller": item.product.seller,
			"quantity": item.quantity,
			"date_added": item.date_added,
			"image": item.product.imageURL,
			"price": item.get_total
		})

	context = {"purchases": purchases}
	return render(request, 'store/purchase_history.html', context)
	
def wishList(request):
	context = {}
	return render(request, 'store/wishList.html', context)

# watchlist is a list of auction items that user watch to see
def watchList(request):
	context = {}
	return render(request, 'store/watchList.html', context)

def userProfile(request):
	if request.method == 'POST':
		user_form = UpdateUserForm(request.POST, instance=request.user.customer)
		user_pic_form = UpdateUserProfilePic(request.POST, request.FILES, instance=request.user.customer)
		if user_form.is_valid() and user_pic_form.is_valid():
			user_form.save()
			user_pic_form.save()
			messages.success(request, f'Your account information has been updated!')
			return redirect('user_profile')
	else:
		user_form = UpdateUserForm(instance=request.user.customer)
		user_pic_form = UpdateUserProfilePic(instance=request.user.customer)
	
	orders = request.user.customer.order_set.all()

	context = {
		'user_form': user_form,
		'user_pic_form': user_pic_form,
		'orders': orders
		}
	return render(request, 'store/user_profile.html', context)

