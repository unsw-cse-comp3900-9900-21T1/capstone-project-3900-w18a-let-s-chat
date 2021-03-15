from django.shortcuts import render, redirect
from .models import *
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.core.mail import EmailMessage
from django.conf import settings
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.http import HttpResponseNotFound
import json
import datetime 
from django.views.generic import TemplateView, ListView
from django.db.models import Q

# Create your views here.
from .forms import OrderForm, CreateUserForm, UpdateUserForm, UpdateUserProfilePic

def store(request):

	if request.user.is_authenticated:
			customer = request.user.customer
			order, created = Order.objects.get_or_create(customer=customer, complete=False)
			items = order.orderitem_set.all()
			cartItems = order.get_cart_items
	else:
		#Create empty cart for now for non-logged in user
		items = []
		order = {'get_cart_total':0, 'get_cart_items':0}
		cartItems = order['get_cart_items']

	products = Product.objects.all()
	context = {'products':products, 'cartItems':cartItems}
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

				messages.success(request, 'Account was created for ' + username)

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

	cartItems = 0
	context = {'form':form, 'cartItems':cartItems}
	return render(request, 'store/signup.html', context)

def signup_success(request):

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
	
	cartItems = 0
	context = {'cartItems':cartItems}
	return render(request, 'store/login.html', context)

def logoutUser(request):
	logout(request)
	return redirect('login')

def product_page(request, slug=None):
	
	product_filter = Product.objects.filter(slug_str=slug)
	if product_filter.count() != 1:
		return HttpResponseNotFound("404: Product listing was not found")
	product = product_filter.first()

	if request.user.is_authenticated:
		customer = request.user.customer
		order, created = Order.objects.get_or_create(customer=customer, complete=False)
		cartItems = order.get_cart_items
	else:
		#Create empty cart for now for non-logged in user
		order = {'get_cart_total':0, 'get_cart_items':0}
		cartItems = order.get('get_cart_items')

	
	context = {"product": product, "tags": product.tags.names(), "cartItems":cartItems}
	return render(request, 'store/product_description.html', context)

def cart(request):

	if request.user.is_authenticated:
		customer = request.user.customer
		order, created = Order.objects.get_or_create(customer=customer, complete=False)
		items = order.orderitem_set.all()
		cartItems = order.get_cart_items
	else:
		#Create empty cart for now for non-logged in user
		items = []
		order = {'get_cart_total':0, 'get_cart_items':0}
		cartItems = order.get('get_cart_items')

	context = {'items':items, 'order':order, 'cartItems':cartItems}
	return render(request, 'store/cart.html', context)

def checkout(request):
	if request.user.is_authenticated:
		customer = request.user.customer
		order, created = Order.objects.get_or_create(customer=customer, complete=False)
		items = order.orderitem_set.all()
		cartItems = order.get_cart_items
	else:
		#Create empty cart for now for non-logged in user
		items = []
		order = {'get_cart_total':0, 'get_cart_items':0}
		cartItems = order.get('get_cart_items')

	context = {'items':items, 'order':order, 'cartItems':cartItems}
	return render(request, 'store/checkout.html', context)

def purchase_history(request):
	if not request.user.is_authenticated:
		return redirect('login')

	customer = request.user.customer
	# order is for cart to update the total number of items in cart
	order, created = Order.objects.get_or_create(customer=customer, complete=False)

	# To query the complete orders
	orders = Order.objects.filter(customer=customer, complete=True)
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

	cartItems = order.get_cart_items
	context = {"purchases": purchases, 'cartItems':cartItems}
	return render(request, 'store/purchase_history.html', context)
	
def wishlist(request):
	context = {}
	return render(request, 'store/wishlist.html', context)

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
	# Please don't delete the next three lines 
	# order is for cart to update the total number of items in cart
	customer = request.user.customer
	order, created = Order.objects.get_or_create(customer=customer, complete=False)
	cartItems = order.get_cart_items

	orders = Order.objects.filter(customer=customer)

	context = {
		'user_form': user_form,
		'user_pic_form': user_pic_form,
		'orders': orders,
		'cartItems':cartItems
		}
	return render(request, 'store/user_profile.html', context)

def updateItem(request):
	data = json.loads(request.body)
	productId = data['productId']
	action = data['action']

	customer = request.user.customer
	product = Product.objects.get(id=productId)
	order, created = Order.objects.get_or_create(customer=customer, complete=False)

	orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

	# run out of stock
	if product.remaining_unit == 0 or product.remaining_unit == orderItem.quantity:
		if action == 'remove':
			orderItem.quantity -= 1

	# Still have enough stock available
	elif product.remaining_unit != 0 and product.remaining_unit > orderItem.quantity:
		if action == 'add':
			orderItem.quantity += 1
		
		elif action == 'remove':
			orderItem.quantity -= 1
	else:
		if action == 'remove':
			orderItem.quantity -= 1

	orderItem.save()
	print('Action:', action)
	print('Product:', productId)

	if orderItem.quantity <= 0:
		orderItem.delete()
		print('delete')
	
	return JsonResponse('Item was updated', safe=False)


def processOrder(request):
	transaction_id = datetime.datetime.now().timestamp()
	data = json.loads(request.body)

	if request.user.is_authenticated:
		customer = request.user.customer
		order, created = Order.objects.get_or_create(customer=customer, complete=False)
		total = float(data['form']['total'])
		order.transaction_id = transaction_id

		# To prevent user change the value through javascript to bypass the checkout checking
		if total == order.get_cart_total:
			order.complete = True
		order.save()

		ShippingAddress.objects.create(
			customer=customer,
			order=order,
			recipient=customer.nickname,
			address=data['shipping']['address'],
			city=data['shipping']['city'],
			state=data['shipping']['state'],
			postcode=data['shipping']['postcode'],
		)

		orderItems =  order.orderitem_set.all()
		for item in orderItems:
			product = Product.objects.get(id=item.product.id)
			product.remaining_unit -= item.quantity
			product.sold_unit += item.quantity
			product.save()			


	return JsonResponse('Payment success', safe=False)

def searchResult(request):
	if request.user.is_authenticated:
		customer = request.user.customer
		order, created = Order.objects.get_or_create(customer=customer, complete=False)
		cartItems = order.get_cart_items
	else:
		#Create empty cart for now for non-logged in user
		order = {'get_cart_total':0, 'get_cart_items':0}
		cartItems = order.get('get_cart_items')

	query = request.GET.get('q')

	if query == "":
		product_list = Product.objects.none()
	else:
		product_list = Product.objects.filter(Q(name__icontains=query)) 

	context = {'product_list':product_list, 'cartItems':cartItems}
	return render(request, 'store/product_list.html', context)
	# return product_list

def add_multiple(request):
	data = json.loads(request.body)

	if request.user.is_authenticated:
		customer = request.user.customer
		order, created = Order.objects.get_or_create(customer=customer, complete=False)
		productId = int(data['productId'])
		quantity = int(data['quantity'])
		print(quantity)
		product = Product.objects.get(id=productId)
		orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

		# Still have enough stock available
		if product.remaining_unit != 0 and product.remaining_unit > orderItem.quantity:
			orderItem.quantity += quantity
			orderItem.save()	


	return JsonResponse('Payment success', safe=False)