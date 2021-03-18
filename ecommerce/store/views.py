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

from .forms import CreateProductForm
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

	# Only get products that still have units left
	products = Product.objects.filter(remaining_unit__gt=0)
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

	context = {'form':form}
	return render(request, 'store/signup.html', context)

def signup_success(request):
	return render(request, 'store/signup_success.html')


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
	
	return render(request, 'store/login.html')

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

		ProductViewCount.log(customer, product)
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
	orders = Order.objects.filter(customer=customer, complete=True).order_by('-transaction_id')
	order_items = OrderItem.objects.filter(order__in=orders).order_by('-date_added')

	purchases = []
	for o in orders:
		order_items = OrderItem.objects.filter(order=o).order_by('-date_added')

		for item in order_items:
			purchases.append({
				"iid":item.id,
				"product":item.product,
				"id":item.product.id,
				"name": item.product.name,
				"seller": item.product.seller.nickname,
				"quantity": item.quantity,
				"date_added": item.date_added,
				"transaction": o.transaction_id,
				"estimated": item.product.delivery_period_days_hours_str,
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

def new_product(request):
	if not request.user.is_authenticated:
		return redirect('login')
	else:

		if request.method == "POST":
			form = CreateProductForm(request.POST, request.FILES)
			if form.is_valid():
				product = form.save()
				product.seller = request.user.customer
				return redirect(f'/product/{product.slug_str}')
		
		else:
			form = CreateProductForm(initial={
				'remaining_unit': 1,
				'price': 10.00,
				'isAnimal': False
			})


		context = {"form": form}
		return render(request, 'store/new_product.html', context)
  
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
	elif query.find("seller:") != -1 :
		sellername = query[7:]
		print("seller wanted: " + sellername)
		if sellername[0] == " ":
			print("there is a space")
			sellername2 = sellername[1:]
			product_list = Product.objects.filter(Q(seller__nickname__icontains=sellername2))
		else:
			product_list = Product.objects.filter(Q(seller__nickname__icontains=sellername))
	
	elif query.find("tags:") != -1:
		tagquery = query[5:]
		tagqueryfinal = tagquery
		
		if tagquery[0] == " ":
			tagqueryfinal = tagquery[1:]
		product_list = Product.objects.none()

		taglist = tagqueryfinal.split(',')

		if len(taglist) == 1:
			product_list = Product.objects.filter(Q(tags__name__icontains=taglist[0]))
		else:

			tmp1 = Product.objects.none()
			tmp2 = Product.objects.none()
			counter = 0;
			for tag in taglist:
				tag_checked = tag
				if tag_checked[0] == " ":
					tag_checked = tag[1:]
				print("Tag is: " + tag_checked)
				if counter == 0:
					tmp2 = Product.objects.filter(Q(tags__name__icontains=tag_checked))
					counter = 1;

				else:
					tmp1 = Product.objects.filter(Q(tags__name__icontains=tag_checked))

					product_list = tmp1 & tmp2

					tmp2 = product_list


			
	else:
		product_list = Product.objects.filter(Q(name__icontains=query))
	
	# Only show products that still have units left
	product_list = product_list.filter(remaining_unit__gt=0)
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
		if product.remaining_unit != 0 and product.remaining_unit > (orderItem.quantity + quantity):
			orderItem.quantity += quantity
			orderItem.save()

		if orderItem.quantity <= 0:
			orderItem.delete()
			print('delete')	

	return JsonResponse('Payment success', safe=False)

def restore(request):
	data = json.loads(request.body)

	customer = request.user.customer
	orders = Order.objects.filter(customer=customer, complete=True)
	order_items = OrderItem.objects.filter(order__in=orders).order_by('-date_added')

	productId = int(data['product'])
	itemId = int(data['itemId'])

	print('pid:', productId)
	print('iid:', itemId)

	for item in order_items:
		if item.product.id == productId and item.id == itemId:
			product = Product.objects.get(id=productId)
			if product != None:
				print(item.quantity)
				product.remaining_unit += item.quantity
				product.sold_unit -= item.quantity
				product.save()
				item.delete()
				print("cancel")
			else:
				print('none')
			break

	return JsonResponse('Cancelled', safe=False)
