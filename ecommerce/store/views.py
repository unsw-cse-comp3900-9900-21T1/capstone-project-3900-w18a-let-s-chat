from __future__ import unicode_literals
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
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
import os
import sys
import json
import datetime
import re
import threading
from uuid import uuid4

from django.views.decorators.csrf import csrf_exempt

from .forms import CreateProductForm
from django.views.generic import TemplateView, ListView
from django.db.models import Q
from django.core.paginator import Paginator
from django.core.exceptions import ObjectDoesNotExist

from .forms import OrderForm, CreateUserForm, UpdateUserForm, UpdateUserProfilePic, EditProductForm
from .recommender import Recommender

### Constants ###

# Max number of similar products to show on product pages
max_similar = 10
# Max number of products to show on recently viewed scroll
max_recent = 10
# Number of products on paginated store pages
paginated_size = 9
# Number of recent orders to display under each product on manage listings page
recent_orders_display_size = 5

#################

def store(request):

    if request.user.is_authenticated:
        customer = request.user.customer
        cartItems = cart_items(customer)

        rec = Recommender(request.user.customer)
        products = rec.get_recommended_products()
        # for p in products:
        #     print(p.name, rec.calculate_similarity(p))

        # Get most recently viewed products - this displays even unlisted items
        view_counts = ProductViewCount.objects.filter(customer=request.user.customer).order_by('-last_viewing')
        recent_products = [view_count.product for view_count in view_counts][:max_recent]

    else:
        cartItems = 0
        # Get all active products for now
        products = Product.objects.filter(is_active=True)
        recent_products = []
    
    # Paginate product list
    paginator = Paginator(products, paginated_size)
    page_number = request.GET.get('page')
    paginated_products = paginator.get_page(page_number)

    context = {'products':paginated_products, 'recent': recent_products, 'cartItems':cartItems}
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
    
    try:
        product = Product.objects.get(slug_str=slug)
    except ObjectDoesNotExist:
        return HttpResponseNotFound('404: Product listing was not found')

    if request.user.is_authenticated:
        customer = request.user.customer
        cartItems = cart_items(customer)

        ProductViewCount.log(customer, product)
    else:
        #Create empty cart for now for non-logged in user
        cartItems = 0

    similar_items = product.tags.similar_objects()[:max_similar]
    similar_items = list(filter(lambda p: p.is_active, similar_items))
    
    context = {
        "product": product,
        "tags": product.tags.names(),
        "cartItems": cartItems,
        "similar_items": similar_items
    }
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
    # cartItems to update the total number of items in cart
    cartItems = cart_items(customer)
    
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

    context = {
        'purchases': purchases,
        'cartItems': cartItems,
        'delivered': orders.count,
        'pending': Order.objects.filter(customer=customer, complete=False).count,
        'total_orders': Order.objects.filter(customer=customer).count
    }
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
    # Please don't delete the next two lines 
    # order is for cart to update the total number of items in cart
    customer = request.user.customer
    cartItems = cart_items(customer)

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
            if product.selling_type == "sale":
                total_price = product.price * item.quantity
            else:
                total_price = product.starting_bid

            seller_template = render_to_string('store/email_processOrder_to_seller.html', {'name': product.seller.nickname, 'product': product.name, 'unit': item.quantity, 'total': total_price})

            print(settings.EMAIL_HOST_USER)
            email = EmailMessage(
                'Your product has been sold!',
                seller_template,
                settings.EMAIL_HOST_USER,
                [product.seller.email],
            )

            email.fail_silently = False
            email.send()

            seller_template = render_to_string('store/email_processOrder_to_buyer.html', {'name': customer.nickname, 'product': product.name, 'unit': item.quantity, 'total': total_price})

            print(settings.EMAIL_HOST_USER)
            email = EmailMessage(
                'Your have purchased a product successfully!',
                seller_template,
                settings.EMAIL_HOST_USER,
                [customer.email],
            )

            email.fail_silently = False
            email.send()

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
                product.save()
                return redirect(f'/product/{product.slug_str}')
        
        else:
            form = CreateProductForm(initial={
                'remaining_unit': 1,
                'price': 10.00,
                'isAnimal': False
            })
        customer = request.user.customer
        cartItems = cart_items(customer)

        context = {"form": form, 'cartItems':cartItems}
        return render(request, 'store/new_product.html', context)
  
def searchResult(request):
    if request.user.is_authenticated:
        customer = request.user.customer
        cartItems = cart_items(customer)
    else:
        cartItems = 0

    query = request.GET.get('q')

    if query == "":
        product_list = Product.objects.none()
    else:
        
        if query.find(",") != -1:
            taglist = query.split(',')

            if len(taglist) == 1:
                product_list = Product.objects.filter(Q(tags__name__icontains=taglist[0]))
            else:

                tmp1 = Product.objects.none()
                tmp2 = Product.objects.none()
                counter = 0
                for tag in taglist:
                    tag_checked = tag
                    if tag_checked[0] == " ":
                        tag_checked = tag[1:]
                    print("Tag is: " + tag_checked)
                    if counter == 0:
                        tmp2 = Product.objects.filter(Q(tags__name__icontains=tag_checked))
                        counter = 1

                    else:
                        tmp1 = Product.objects.filter(Q(tags__name__icontains=tag_checked))

                        product_list = tmp1 & tmp2

                        tmp2 = product_list

        else:
            product_list = Product.objects.filter(Q(name__icontains=query))
            if not product_list:
                product_list = Product.objects.filter(Q(seller__nickname__icontains=query))

                if not product_list:
                    product_list = Product.objects.filter(Q(tags__name__icontains=query))

    # Only show products that still have units left and aren't unlisted
    product_list = product_list.filter(remaining_unit__gt=0, is_active=True).distinct()
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
        try:
            product = Product.objects.get(id=productId)
        except ObjectDoesNotExist:
            return JsonResponse('Product not found', safe=False)
        if not product.is_active:
            return JsonResponse('Product is unlisted', safe=False)

        orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

        # Still have enough stock available
        if product.remaining_unit != 0 and product.remaining_unit >= (orderItem.quantity + quantity):
            orderItem.quantity += quantity
            orderItem.save()

        if orderItem.quantity <= 0:
            orderItem.delete()
            print('delete')	

    return JsonResponse('added', safe=False)

def restore(request):
    data = json.loads(request.body)

    customer = request.user.customer
    orders = Order.objects.filter(customer=customer, complete=True)
    order_items = OrderItem.objects.filter(order__in=orders).order_by('-date_added')

    productId = int(data['product'])
    itemId = int(data['itemId'])

    # print('pid:', productId)
    # print('iid:', itemId)

    for item in order_items:
        if item.product.id == productId and item.id == itemId:
    
            try:
                product = Product.objects.get(id=productId)
                # print(item.quantity)
                product.remaining_unit += item.quantity
                product.sold_unit -= item.quantity
                product.save()
                item.delete()
                # print("cancel")
            except Product.DoesNotExist:
                print('none')
            break

    return JsonResponse('Cancelled', safe=False)

def my_listings(request):
    if not request.user.is_authenticated:
        return redirect('login')

    # order is for cart to update the total number of items in cart
    customer = request.user.customer
    cartItems = cart_items(customer)

    products = Product.objects.filter(seller=customer)
    items = []
    # Get most recent orders of each product
    for product in products:
        order_items = OrderItem.objects.filter(product=product).order_by('-date_added')
        items.append({
            'product': product,
            'recent_orders': order_items[:recent_orders_display_size],
            'n_orders': order_items.count()
        })


    context = {'items': items, 'cartItems':cartItems}
    return render(request, 'store/my_listings.html', context)

def view_orders(request, slug=None):
    if not request.user.is_authenticated:
        return redirect('login')
    try:
        product = Product.objects.get(slug_str=slug)
    except ObjectDoesNotExist:
        return HttpResponseNotFound('404: Product listing was not found')
    if product.seller != request.user.customer:
        return HttpResponseForbidden('403: Can only view orders for your own listings')

    order_items = OrderItem.objects.filter(product=product).order_by('-date_added')
    paginator = Paginator(order_items, 100)
    page_number = request.GET.get('page')
    paginated_order_items = paginator.get_page(page_number)
    cartItems = cart_items(request.user.customer)
    context = {
        'product': product,
        'order_items': paginated_order_items,
        'cartItems': cartItems
    }
    return render(request, 'store/view_orders.html', context)

def edit_listing(request, slug=None):
    if not request.user.is_authenticated:
        return redirect('login')
    try:
        product = Product.objects.get(slug_str=slug)
    except ObjectDoesNotExist:
        return HttpResponseNotFound('404: Product listing was not found')
    if product.seller != request.user.customer:
        return HttpResponseForbidden('403: Can only edit your own listings')


    if request.method == 'POST':
        form = EditProductForm(request.POST)
        if form.is_valid():
            # Update field in product that was not left blank on form
            print(form.cleaned_data)
            if form.cleaned_data['name']:
                product.name = form.cleaned_data['name']
            if form.cleaned_data['price']:
                product.price = form.cleaned_data['price']
            if form.cleaned_data['end_date']:
                product.end_date = form.cleaned_data['end_date']
            if form.cleaned_data['remaining_unit']:
                product.remaining_unit = form.cleaned_data['remaining_unit']
            if form.cleaned_data['description']:
                product.description = form.cleaned_data['description']
            if form.cleaned_data['tags'] or form.cleaned_data['clear_existing_tags']:
                product.tags.set(*form.cleaned_data['tags'], clear=form.cleaned_data['clear_existing_tags'])

            product.save()
            return redirect('my_listings')
    else:
        form = EditProductForm()
        # Set placeholder text on fields to product's old values
        form.fields['name'].widget.attrs['placeholder'] = product.name
        form.fields['price'].widget.attrs['placeholder'] = product.price
        form.fields['remaining_unit'].widget.attrs['placeholder'] = product.remaining_unit
        form.fields['description'].widget.attrs['placeholder'] = product.description
        form.fields['tags'].widget.attrs['placeholder'] = ', '.join(product.tags.names())


    cartItems = cart_items(request.user.customer)
    context = {
        'form': form,
        'product': product,
        'cartItems':cartItems
    }
    return render(request, 'store/edit_listing.html', context)

def toggle_unlist(request):
    if not request.user.is_authenticated:
        return JsonResponse(data={}, status=401)
    try:
        slug = request.POST.get('slug_str', '')
        product = Product.objects.get(slug_str=slug)
    except ObjectDoesNotExist:
        return JsonResponse(data={}, status=404)
    if product.seller != request.user.customer:
        return JsonResponse(data={}, status=403)
    
    product.is_active = not product.is_active
    product.save()
    
    return redirect('my_listings')

# ---------------------Chatbot section-------------------------#

@csrf_exempt
def webhook(request):
    
    if (request.method == 'POST'):

        print('Received a post request')

        body_unicode = request.body.decode('utf-8')
        req = json.loads(body_unicode)

        action = req.get('queryResult').get('action')
        parameters = req.get('queryResult').get('parameters')
        # parameters is dict
        print(parameters)
        print(action)
        message = "ok"
        if action == 'product_enquiry':
            inquiry = parameters.get('product_details')
            product = inquiry_product(parameters)
            
            if product == '':
                message = 'Sorry, please tell me which product you want to know.'
            else:
                
                try:
                    matched_product = Product.objects.get(name=product)
                except Product.DoesNotExist:
                    message = "Sorry, {} cannot be found.".format(product)
                    responseObj = {
                        "fulfillmentText":  message,
                        "source": ""
                    }
                    return JsonResponse(responseObj)
            
                matched_product = Product.objects.get(name=product)
                    
                if inquiry == 'warranty':
                    warranty = matched_product.warranty
                    print(warranty)
                    if warranty == 'No warranty':
                        message = "{} has no warranty.".format(product)
                    else:
                        message = "Warranty of {} is {}".format(product, warranty)
                elif inquiry == 'delivery date':
                    
                    delivery = matched_product.delivery_period_days_hours_str
                    if delivery == None:
                        message = "Seller has not provided any estimated delivery date for {}.".format(product)
                    else:
                        message = "Delivery period for {} is {}".format(product, delivery)
                elif inquiry == 'details':
                    description = matched_product.description
                    if description == '':
                        message = "Seller has not provided any description for {}.".format(product)
                    else:
                        message = "{}:\n{}".format(product, description)
                else:
                    message = 'Sorry I cannot understand your questions. Please ask me again.'
                


        responseObj = {
            "fulfillmentText":  message,
            # "fulfillmentMessages": [{"text": {"text": [message]}}],
             "source": ""
        }
        return JsonResponse(responseObj)

    return HttpResponse('OK')


def inquiry_product (parameters):
    product = ''
    if parameters.get('collar') != '':
        product =parameters.get('collar')
        
    elif parameters.get('toy') != '':
        product =parameters.get('toy')
        
    elif parameters.get('dog') != '':
        product =parameters.get('dog')
        
    elif parameters.get('pet_food') != '':
        product =parameters.get('pet_food')
    
    return product

def cart_items (customer):
    order, created = Order.objects.get_or_create(customer=customer, complete=False)
    items = order.orderitem_set.all()
    items = order.get_cart_items
    
    return items
def add_bid(request):
	data = json.loads(request.body)
	if request.user.is_authenticated:
		customer = request.user.customer
		order, created = Order.objects.get_or_create(customer=customer, complete=False)
		all_customer = Customer.objects.all()
		productId = int(data['productId'])
		new_bid = int(data['new_bid'])
		for each_customer in all_customer:
			if each_customer.nickname == data['highest_bidder']:
				highest_bidder = each_customer
				
		try:
			product = Product.objects.get(id=productId)
		except ObjectDoesNotExist:
			return JsonResponse('Product not found', safe=False)
		if not product.is_active:
			return JsonResponse('Product is unlisted', safe=False)

		if new_bid > product.starting_bid:
			product.starting_bid = new_bid
			product.highest_bidder = highest_bidder
			messages.success(request, f'You have successfully placed a bid!')
			product.save()
			return JsonResponse('You have successfully placed a bid!', safe=False)
		else:
			messages.error(request, f'The bid must be greater than the current bid!')
			return JsonResponse('The bid must be greater than the current bid!', safe=False)

def check_auction_time():
	threading.Timer(10.0, check_auction_time).start()
	# print("checking auction time")
	products = Product.objects.all()
	for product in products:
		if product.is_active == True:
			if product.selling_type == "auction":
				if datetime.datetime.utcnow() >= product.end_date.replace(tzinfo=None):
					print("datetime_now: " + str(datetime.datetime.now()))
					print("end_date: " + str(product.end_date.replace(tzinfo=None)))
					bidder = product.highest_bidder
					order, created = Order.objects.get_or_create(customer=bidder, complete=False)

					orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)
					orderItem.quantity += 1
					orderItem.save()

					product.is_active = False
					product.save()
					seller_template = render_to_string('store/email_auctionEnd_to_buyer.html', {'name': product.highest_bidder.nickname, 'product': product.name, 'price': product.starting_bid})

					email = EmailMessage(
						'You have win the Auction!',
						seller_template,
						settings.EMAIL_HOST_USER,
						[product.highest_bidder.email],
					)

					email.fail_silently = False
					email.send()

					seller_template = render_to_string('store/email_processOrder_to_seller.html', {'name': product.seller.nickname, 'bidder': product.highest_bidder.nickname, 'product': product.name, 'price': product.starting_bid})

					print(settings.EMAIL_HOST_USER)
					email = EmailMessage(
						'Your product has ended!',
						seller_template,
						settings.EMAIL_HOST_USER,
						[product.seller.email],
					)

					email.fail_silently = False
					email.send()

# check_auction_time()
