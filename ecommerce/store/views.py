'''
View functions corresponding to site urls
'''

from __future__ import unicode_literals
from django.shortcuts import render, redirect
from .models import *
from django.utils import timezone
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
import base64
import re
import threading
from uuid import uuid4

from django.views.decorators.csrf import csrf_exempt

from .filters import ProductFilter 
from .forms import CreateProductForm
from django.views.generic import TemplateView, ListView
from django.db.models import Q
from django.core.paginator import Paginator
from django.core.exceptions import ObjectDoesNotExist

from .forms import OrderForm, CreateUserForm, UpdateUserForm, UpdateUserProfilePic, EditProductForm, NewReviewForm
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
# Customer
ca = None

#################

def store(request):
    '''
    Path: '/', GET request

    Render the main store page with recommended products and recently viewed items.
    Recommended products are retrieved using recommender system and are paginated

    Returns a rendered HTML template as a HTTPResponse
    '''

    context = {}
    if request.user.is_authenticated:
        customer = request.user.customer
        ca = customer
        cartItems = cart_items(customer)
        

        # Get most recently viewed products - this displays even unlisted items
        view_counts = ProductViewCount.objects.filter(customer=request.user.customer).order_by('-last_viewing')
        recent_products = [view_count.product for view_count in view_counts][:max_recent]

        context['customer'] = customer
    else:
        cartItems = 0
        recent_products = []

    # Get products from recommender
    rec = Recommender(customer=request.user.customer if request.user.is_authenticated else None)
    products = rec.get_recommended_products()
    
    # Paginate product list
    paginator = Paginator(products, paginated_size)
    page_number = request.GET.get('page')
    paginated_products = paginator.get_page(page_number)

    context.update({'products':paginated_products, 'recent': recent_products, 'cartItems':cartItems})
    return render(request, 'store/store.html', context)

def signup(request):
    '''
    Path: 'signup/', GET and POST request

    - If GET request, render the signup page with signup form
    - If POST request and form is valid, create new user, send confirmation email and redirect to signup success page

    Returns a rendered HTML template as a HTTPResponse
    '''

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
                wishlist = Wishlist()
                customer.wishlist = wishlist
                wishlist.customer = customer
                customer.save()
                wishlist.save()

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
    '''
    Path: 'signup_success/', GET request

    Returns a rendered HTML template as a HTTPResponse
    '''


    return render(request, 'store/signup_success.html')


def loginPage(request):
    '''
    Path: '/login', GET and POST request

    - If GET request, render the login page with login form
    - If POST request and form is valid, authenticate the user with session based auth, and redirect to store page

    Returns a rendered HTML templase as a HTTPResponse
    '''

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
    '''
    Path: 'logout/', POST request

    Invalidate user's login session and redirect to login page

    Returns a rendered HTML template as HTTPResponse
    '''

    logout(request)
    return redirect('login')

def product_page(request, slug=None):
    '''
    Path: 'product/<slug string>', GET request

    Render a product listing's store page, which includes:
    - Details of the product
    - Similar listings, found using tag similarity
    - Reviews for the product

    Returns a rendered HTML template as HTTPResponse
    '''

    context = {}
    try:
        product = Product.objects.get(slug_str=slug)
    except ObjectDoesNotExist:
        return HttpResponseNotFound('404: Product listing was not found')

    if request.user.is_authenticated:
        customer = request.user.customer
        cartItems = cart_items(customer)
        is_owner = customer == product.seller
        ProductViewCount.log(customer, product)
        try:
            user_review = product.reviews.get(author=customer)
        except ObjectDoesNotExist:
            user_review = None
        
        # Get all of the user's reacts to reviews for this product
        user_reacts = ReviewReact.objects.filter(customer=request.user.customer, review__product=product)
        context['customer'] = customer
        context['seller'] = Customer.objects.get(slug_str=product.seller.slug_str)
        
    else:
        #Create empty cart for now for non-logged in user
        cartItems = 0
        is_owner = False
        user_review = None

    similar_items = product.tags.similar_objects()[:max_similar]
    similar_items = list(filter(lambda p: p.is_active, similar_items))
    
    # Get initial state of like and dislike buttons for each review
    reviews = []
    for review in product.reviews.all():
        liked = False
        disliked = False
        if request.user.is_authenticated:
            try:
                react = user_reacts.get(review=review)
                liked = react.liked
                disliked = not liked
            except ObjectDoesNotExist:
                pass
        reviews.append({
            "review": review,
            "liked": liked,
            "disliked": disliked,
            "verified": OrderItem.objects.filter(product=product, order__customer=review.author, order__complete=True).exists()
        })

    context.update({
        "product": product,
        "tags": product.tags.names(),
        "cartItems": cartItems,
        "similar_items": similar_items,
        "is_owner": is_owner,
        "user_review": user_review,
        "reviews": reviews
    })
    return render(request, 'store/product_description.html', context)

def cart(request):
    '''
    Path: 'cart/', GET request, requires login

    Render a user's current cart, with buttons to change item quantities and 

    Returns a rendered HTML template as HTTPResponse
    '''

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
    '''
    Path: 'checkout/', GET request, requires login

    Render the checkout form for an order.

    Returns a rendered HTML template as HTTPResponse
    '''

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
    '''
    Path: 'purchase_history/', GET request, requires login

    Render a user's purchase history page, showing details of ordered items
    
    Returns a rendered HTML template as HTTPResponse
    '''

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
        # print(order_items.estimated_date)
        for item in order_items:
            purchases.append({
                "iid":item.id,
                "product":item.product,
                "id":item.product.id,
                "name": item.product.name,
                "seller": item.product.seller.nickname,
                "quantity": item.quantity,
                "date_ordered": o.date_ordered,
                "transaction": o.transaction_id,
                "estimated": item.product.estimated_date,
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
    
# Wishlist and Watchlist is now in the same page
def wishlist(request):
    '''
    Path: 'wishlist/', GET request, requires login

    Render the wishlist page for a user, which shows details on wishlisted items,
    as well as auctions the user is watching

    Returns a rendered HTML template as HTTPResponse
    '''
    if not request.user.is_authenticated:
        return redirect('login')

    customer = request.user.customer
    # cartItems to update the total number of items in cart
    cartItems = cart_items(customer)
    
    # To query the complete orders
    wishlist = customer.wishlist.product.all()

    items = []
    for item in wishlist:
        items.append({
            "id":item.id,
            "selling_type": item.selling_type,
            "is_active": item.is_active,
            "product":item,
            "name": item.name,
            "current_bid": item.starting_bid,
            "seller": item.seller.nickname,
            "remaining_unit": item.remaining_unit,
            "image": item.imageURL,
            "price": item.price
        })

    context = {
        'items': items,
        'cartItems': cartItems,
        'pending': Order.objects.filter(customer=customer, complete=False).count,
        'total_orders': Order.objects.filter(customer=customer).count
    }
    return render(request, 'store/wishlist.html', context)

def userProfile(request, slug=None):
    '''
    Path: 'profile/', GET or POST request, requires login

    - If GET request, render a user's profile page with form for changing details
    - If POST request and form is valid, update the user's details and reload the page

    Returns a rendered HTML template as HTTPResponse
    '''
    if request.method == 'POST':
        user_form = UpdateUserForm(request.POST, instance=request.user.customer)
        user_pic_form = UpdateUserProfilePic(request.POST, request.FILES, instance=request.user.customer)
        if user_form.is_valid() and user_pic_form.is_valid():
            user_form.save()
            user_pic_form.save()
            # messages.success(request, f'Your account information has been updated!')
            return redirect(f'/user_profile/{slug}')
    else:
        user_form = UpdateUserForm(instance=request.user.customer)
        user_pic_form = UpdateUserProfilePic(instance=request.user.customer)
    
    orders = request.user.customer.order_set.all()
    # Please don't delete the next two lines 
    # order is for cart to update the total number of items in cart
    customer = request.user.customer
    customer_match = Customer.objects.get(slug_str=slug)
    cartItems = cart_items(customer)

    orders = Order.objects.filter(customer=customer)

    items = []
    products = Product.objects.all()
    for product in products:
        if product.seller == customer_match:
            items.append(product)

    context = {
        'customer': customer_match,
        'items': items,
        'user_form': user_form,
        'user_pic_form': user_pic_form,
        'orders': orders,
        'cartItems':cartItems
        }
    return render(request, 'store/user_profile.html', context)

def updateItem(request):
    '''
    Path: 'update_item/', POST request, requires login

    Update the state of an order item in an order

    Returns a JsonResponse object
    '''
    data = json.loads(request.body)
    productId = data['productId']
    action = data['action']

    customer = request.user.customer
    update_cart(action, productId, customer)
    
    return JsonResponse('Item was updated', safe=False)


def processOrder(request):
    '''
    Path: 'process_order/', POST request, requires login

    Complete the purchase of an order using dummy payment system, and send an
    email notification to both the seller and buyer

    Returns a JSONResponse object
    '''

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
            order.date_ordered = timezone.now()
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
            product.estimated_date = timezone.now() + product.delivery_period
            product.save()			
            if product.selling_type == "sale":
                total_price = product.price * item.quantity
            else:
                total_price = product.starting_bid

            # seller_template = render_to_string('store/email_processOrder_to_seller.html', {'name': product.seller.nickname, 'product': product.name, 'unit': item.quantity, 'total': total_price})

            # email = EmailMessage(
            #     'Your product has been sold!',
            #     seller_template,
            #     settings.EMAIL_HOST_USER,
            #     [product.seller.email],
            # )

            # email.fail_silently = False
            # email.send()

            # seller_template = render_to_string('store/email_processOrder_to_buyer.html', {'name': customer.nickname, 'product': product.name, 'unit': item.quantity, 'total': total_price})

            # email = EmailMessage(
            #     'Your have purchased a product successfully!',
            #     seller_template,
            #     settings.EMAIL_HOST_USER,
            #     [customer.email],
            # )

            # email.fail_silently = False
            # email.send()

    return JsonResponse('Payment success', safe=False)

def new_product(request):
    '''
    Path: 'new_product/', GET and POST request, requires login

    - If GET request, render the new product form
    - If POST request and product form is valid, create the new product and redirect to its product page

    Returns a rendered HTML template as a HTTPResponse
    '''
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
    '''
    Path: 'search_result/', GET request

    Process a search query and render the search page with results

    Return a rendered HTML template as a HTTPResponse
    '''

    if request.user.is_authenticated:
        customer = request.user.customer
        cartItems = cart_items(customer)
    else:
        cartItems = 0

    query = request.GET.get('q')
    if query is None:
        query = request.GET.get('cached_q')
    product_list = query_result(query)

    advancedFilter = ProductFilter(request.GET, queryset=product_list)
    product_list = advancedFilter.qs
    customer = request.user.customer

    context = {'product_list':product_list, 'cartItems':cartItems,'myFilter':advancedFilter, 'query':query, 'customer':customer}
    return render(request, 'store/product_list.html', context)
    # return product_list

def add_multiple(request):
    '''
    Path: 'add_multiple/', POST request, requires login

    Add a given quantity of a product to a user's cart

    Returns a JSONResponse object
    '''
    data = json.loads(request.body)

    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
        productId = int(data['productId'])
        quantity = int(data['quantity'])
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

    return JsonResponse('added', safe=False)

def restore(request):
    '''
    Path: 'restore/', POST request, requires login

    Cancel an order, restoring the quantity of available units for products in the order

    Returns a JSONResponse object 
    '''
    data = json.loads(request.body)

    customer = request.user.customer
    orders = Order.objects.filter(customer=customer, complete=True)
    order_items = OrderItem.objects.filter(order__in=orders).order_by('-date_added')

    productId = int(data['product'])
    itemId = int(data['itemId'])


    for item in order_items:
        if item.product.id == productId and item.id == itemId:
    
            try:
                product = Product.objects.get(id=productId)
                product.remaining_unit += item.quantity
                product.sold_unit -= item.quantity
                product.save()
                item.delete()
            except Product.DoesNotExist:
                print('none')
            break

    return JsonResponse('Cancelled', safe=False)

def my_listings(request):
    '''
    Path: 'my_listings/', GET request, requires login

    Render a user's 'my listings' page which allows viewing and modification of their listed products

    Returns a rendered HTML template as a HTTPResponse
    '''

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
    '''
    Path: 'view_orders/<slug string>', GET request, requires login

    Render the orders page for a user's product, which displays all orders of the product in a table

    Returns a rendered HTML template as a HTTPResponse
    '''
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
    '''
    Path: 'edit_listing/', GET and POST request, requires login

    - If GET request, render the edit listing form, populating field placeholders with the product's current field values
    - If POST request and form is valid, update the product's fields with the values given. Empty form fields are left unmodified.
     Finally, redirect to the my_listings page.

    Returns a rendered HTML template as a HTTPResponse
    '''
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
            if form.cleaned_data['name']:
                product.name = form.cleaned_data['name']
            if form.cleaned_data['price']:
                product.price = form.cleaned_data['price']
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
    '''
    Path: 'toggle_unlist/', POST request, requires login

    Toggle whether the given product is unlisted. Only succeeds if called by owner of product

    Returns a JSONResponse object
    '''

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
    
    return JsonResponse(data={}, status=200)

# ---------------------Chatbot section-------------------------#

@csrf_exempt
def webhook(request):
    '''
    Path: 'webhook/', POST request

    Hook for generating the Dialogflow chatbot's responses to queries

    Returns a JSONResponse object if POST request, else a HTTPResponse
    '''
    
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
                "fulfillmentText": message,
                # "fulfillmentMessages": [{"text": {"text": [message]}}],
                "source": ""
            }          

        elif action == 'product_searching':
            inquiry = parameters.get('product')
            print(inquiry)
            keyword = inquiry_product(parameters)

            if keyword == '':
                responseObj = {
                    "fulfillmentText": "Sorry, I can't found the thing you want. Please ask for something else.",
                    # "fulfillmentMessages": [{"text": {"text": [message]}}],
                    "source": ""
                }   
            else: 
                
                product_list = find_by_tag(keyword)
                print(product_list)
                if not product_list:
                    responseObj = {
                        "fulfillmentText": "Sorry, currently the product that you're searching for is out of stock.",
                        # "fulfillmentMessages": [{"text": {"text": [message]}}],
                        "source": ""
                    }   
                else:
                    elements = create_element(product_list) 
                    responseObj = {
                        "fulfillmentMessages": [{
                            "payload": {
                                "message": "Here you go",
                                "platform": "kommunicate",
                                "metadata": {
                                    "contentType": "300",
                                    "templateId": "7",
                                    "payload": {
                                        "elements": elements,
                                        "headerText": "Here is the searched results"
                                    }
                                }
                            }             
                        }]
                    }
                    print("success")

        elif action == 'place_bid':
            product_name = parameters.get('product_name')
            bid_price = parameters.get('bid_price')
            customer_name = parameters.get('customer_name')
            product = Product.objects.get(name=product_name)

            if not product.is_active:
                message = "This auction is ended!"
            
            elif product.selling_type == 'sale':
                message = "This product isn't an auction product! You can't place a bid for this."

            elif bid_price > product.starting_bid:
                if customer_name == product.seller.nickname:
                    message = "You cannot place a bid to your own product!"

                else:
                    product.starting_bid = bid_price
                    all_customer = Customer.objects.all()
                    for customer in all_customer:
                        if customer.nickname == customer_name:
                            product.highest_bidder = customer
                            product.bidder.create(name=customer_name, price=bid_price)
                            break
                    message = 'You have successfully placed a bid!'
                    product.save()
                    
            else:
                message = f"Your bid price is not greater than the current highest bid price: ${product.starting_bid}!"

            responseObj = {
                "fulfillmentText": message,
                # "fulfillmentMessages": [{"text": {"text": [message]}}],
                "source": ""
            }   
            
        return JsonResponse(responseObj)

    return HttpResponse('OK')


def inquiry_product (parameters):
    '''
    Helper Function to retrieve the correct value from the parsed in parameter dict of Dialogflow
    
    Returns a string
    '''
    product = ''
    if parameters.get('collar') != '':
        product =parameters.get('collar')
        
    elif parameters.get('toy') != '':
        product =parameters.get('toy')
        
    elif parameters.get('dog') != '':
        product =parameters.get('dog')
        
    elif parameters.get('pet_food') != '':
        product =parameters.get('pet_food')

    elif parameters.get('bowl') != '':
        product =parameters.get('bowl')

    elif parameters.get('aquarium') != '':
        product =parameters.get('aquarium')
    
    return product

def cart_items (customer):
    '''
    Helper Function to retrieve number of items in cart so that the cart icon number get to update
    
    Returns a dict
    '''
    order, created = Order.objects.get_or_create(customer=customer, complete=False)
    items = order.orderitem_set.all()
    items = order.get_cart_items
    
    return items

def add_bid(request):
    '''
    Path: 'add_bid/', POST request, requires login

    Add a bid to an auction

    Returns a JSONResponse object
    '''

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
            if customer == product.seller:
                messages.error(request, f'You cannot place a bid to your own product!')
                return JsonResponse('The bid must be greater than the current bid!', safe=False)
            else:
                product.starting_bid = new_bid
                product.highest_bidder = highest_bidder
                product.bidder.create(name=highest_bidder.nickname, price=new_bid)
                messages.success(request, f'You have successfully placed a bid!')
                # product.bidder.save()
                product.save()
                return JsonResponse('You have successfully placed a bid!', safe=False)
        else:
            messages.error(request, f'The bid must be greater than the current bid!')
            return JsonResponse('The bid must be greater than the current bid!', safe=False)

def check_auction_time():
    '''
    Periodically check whether any auctions have ended, and if so,
    process the purchase by the highest bidder
    '''

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

                    seller_template = render_to_string('store/email_auctionEnd_to_seller.html', {'name': product.seller.nickname, 'product': product.name, 'bidder': product.highest_bidder.nickname, 'price': product.starting_bid})

                    print(settings.EMAIL_HOST_USER)
                    email = EmailMessage(
                        'Your auction has ended!',
                        seller_template,
                        settings.EMAIL_HOST_USER,
                        [product.seller.email],
                    )

                    email.fail_silently = False
                    email.send()

def post_new_review(request):
    '''
    Path: 'new_review/', POST request, requires login

    If the given values are valid, submit a new review for a product, composed
    of a text review and a numerical rating

    Returns a JSONResponse object
    '''

    if not request.user.is_authenticated:
        return JsonResponse(data={}, status=401)
    if not request.method == 'POST':
        return JsonResponse(data={}, status=400)
    
    form = NewReviewForm(request.POST)
    if form.is_valid():

        if ProductReview.objects.filter(product__slug_str=form.cleaned_data['slug_str'], author=request.user.customer).exists():
            return JsonResponse(data={}, status=400)

        review = ProductReview(
            product=Product.objects.get(slug_str=form.cleaned_data['slug_str']),
            author=request.user.customer,
            rating=form.cleaned_data['rating'],
            text=form.cleaned_data['text']
        )
        review.save()
        # User automatically likes their own review
        self_react = ReviewReact(liked=True,review=review, customer=request.user.customer)
        self_react.save()

        return JsonResponse(data={}, status=200)


    return JsonResponse(data={}, status=400)

def delete_review(request):
    '''
    Path: 'delete_review/', POST request, requires login

    Remove a product review.

    Returns a JSONResponse object
    '''

    if not request.user.is_authenticated:
        return JsonResponse(data={}, status=401)
    if not request.method == 'POST':
        return JsonResponse(data={}, status=400)

    try:
        review = ProductReview.objects.get(
            product__slug_str=request.POST.get('slug_str'),
            author=request.user.customer)
    except ObjectDoesNotExist:
        return JsonResponse(data={}, status=400)
    
    review.delete()
    return JsonResponse(data={}, status=200)

def edit_review(request):
    '''
    Path: 'edit_review/', POST request, requires login

    If the given values are valid, update the text and rating of a porduct review

    Returns a JSONResponse object
    '''
    if not request.user.is_authenticated:
        return JsonResponse(data={}, status=401)
    if not request.method == 'POST':
        return JsonResponse(data={}, status=400)

    form = NewReviewForm(request.POST)
    if form.is_valid():
        try:
            review = ProductReview.objects.get(
                product__slug_str=form.cleaned_data['slug_str'],
                author=request.user.customer)
        except ObjectDoesNotExist:
            return JsonResponse(data={}, status=400)
        
        review.text = form.cleaned_data['text']
        review.rating = form.cleaned_data['rating']
        review.edited = True
        review.save()

        return JsonResponse(data={}, status=200)
    
    return JsonResponse(data={}, status=400)

def toggle_review_react(request):
    '''
    Path: 'toggle_review_react/', POST request, requires login

    Update whether a user is liking or disliking a product review (or neither). The is_like parameter
    determines whether the like or dislike button was pressed.
    The returned json response contains the review's updated score and react state

    Returns a JSONResponse object
    '''

    if not request.user.is_authenticated:
        return JsonResponse(data={}, status=401)
    if not request.method == 'POST':
        return JsonResponse(data={}, status=400)

    try:
        review = ProductReview.objects.get(id=int(request.POST.get('review_id')))
    except ObjectDoesNotExist:
        return JsonResponse(data={}, status=400)
    
    try:
        react = ReviewReact.objects.get(review=review, customer=request.user.customer)
    except ObjectDoesNotExist:
        react = None

    is_like = request.POST.get('is_like') == 'true'
    if (react is None):
        react = ReviewReact(
            review=review,
            customer=request.user.customer,
            liked=is_like
        )
        react.save()
        state = 'liked' if is_like else 'disliked'

    else:
        # Case where cancelling reaction
        if is_like == react.liked:
            react.delete()
            state = 'neither'
        # Case where switching reaction
        else:
            react.liked = not react.liked
            state = 'liked' if react.liked else 'disliked'
            react.save()
    
    return JsonResponse(data={'score':review.score, 'state':state}, status=200)

def add_wishlist(request):
    '''
    Path: 'add_wishlist/', POST request, requires login

    Add the given item to the user's wishlist

    Returns a JSONResponse object
    '''

    data = json.loads(request.body)
    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
        all_customer = Customer.objects.all()
        productId = int(data['productId'])
        wishlist = customer.wishlist
                
        try:
            product = Product.objects.get(id=productId)
        except ObjectDoesNotExist:
            return JsonResponse('Product not found', safe=False)
        if not product.is_active:
            return JsonResponse('Product is unlisted', safe=False)

        for wish_item in wishlist.product.all():
            if product == wish_item:
                wishlist.product.remove(product)
                wishlist.save()
                print("Removing product_id: " + str(productId))
                print("Removing product name:" + product.name)
                if product.selling_type == "sale":
                    # messages.success(request, f'You have remove a product in your wishlist!')
                    return JsonResponse('You have remove a product in your wishlist!', safe=False)
                else:
                    # messages.success(request, f'You have remove a product in your watchlist!')
                    return JsonResponse('You have remove a product in your watchlist!', safe=False)

        print("Adding product_id: " + str(productId))
        print("Adding product name:" + product.name)
        customer.wishlist.product.add(product)
        wishlist.save()
        if product.selling_type == "sale":
            # messages.success(request, f'You have added a product in your wishlist!')
            return JsonResponse('You have added a product in your wishlist!', safe=False)
        else:
            # messages.success(request, f'You have added a product in your watchlist!')
            return JsonResponse('You have added a product in your watchlist!', safe=False)

def remove_wishlist(request):
    '''
    Path: 'remove_wishlist/', POST request, requires login

    Remove the given item from the user's wishlist

    Returns a JSONResponse object
    '''

    data = json.loads(request.body)
    print("In views.py remove_wishlist")
    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
        all_customer = Customer.objects.all()
        productId = int(data['productId'])
        print("Removing product_id: " + str(productId))
        wishlist = customer.wishlist

        try:
            product = Product.objects.get(id=productId)
            print("Creating product")
        except ObjectDoesNotExist:
            print("ObjectDoesNotExist")
            return JsonResponse('Product not found', safe=False)

        print("Removing product name:" + product.name)
        customer.wishlist.product.remove(product)
        wishlist.save()
        # messages.success(request, f'You have removed a product in your wishlist!')

        return JsonResponse('You have removed a product in your wishlist!', safe=False)

def query_result (query):
    '''
    Helper Function for searchResult 
    This will query the matched results based on product name, tag and seller
    
    Returns a list
    '''
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

                    if counter == 0:
                        tmp2 = Product.objects.filter(Q(tags__name__icontains=tag_checked))
                        counter = 1

                    else:
                        tmp1 = Product.objects.filter(Q(tags__name__icontains=tag_checked))

                        product_list = tmp1 & tmp2

                        tmp2 = product_list

        else:
            product_list = Product.objects.filter(Q(name__icontains=query)|Q(tags__name__icontains=query)|Q(seller__nickname__icontains=query))
            # Only show products that still have units left and aren't unlisted
            product_list = product_list.filter(remaining_unit__gt=0, is_active=True).distinct()
            
        return product_list

def create_element (product_list):
    '''
    Helper Function to create a displayable list in chatbot
    
    Returns a dict
    '''
    elements = []
    for product in product_list:
        # print(image)
        elements.append({
        "title": product.name,
        "description": product.description,
        # "imgSrc": json.dumps(str(product.image)),
        "imgSrc": product.imageUri,
        "action": 
            {
                "type": "link",
                "url": f"http://127.0.0.1:8000/product/{product.slug_str}/"
            }
        })
    

    return elements

def find_by_tag (keyword):
    '''
    Helper Function to search all products that has the desired tag
    
    Returns a list
    '''
    product_list = Product.objects.filter(Q(tags__name__iexact=keyword))
    product_list = product_list.filter(remaining_unit__gt=0, is_active=True).distinct()
    return product_list
    

def update_cart (action, productId, customer):
    '''
    Helper Function to update the cart item like add to cart and remove from cart
    '''
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

    if orderItem.quantity <= 0:
        orderItem.delete()

check_auction_time()
check_auction_time()
