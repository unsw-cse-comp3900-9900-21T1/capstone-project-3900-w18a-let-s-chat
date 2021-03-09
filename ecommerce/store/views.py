from django.shortcuts import render

# Create your views here.

def registration(request):
	context = {}
	return render(request, 'store/registration.html', context)

def login(request):
	context = {}
	return render(request, 'store/login.html', context)

def store(request):
	context = {}
	return render(request, 'store/store.html', context)

def product_description(request):
	context = {}
	return render(request, 'store/product_description.html', context)

def cart(request):
	context = {}
	return render(request, 'store/cart.html', context)

def checkout(request):
	context = {}
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
