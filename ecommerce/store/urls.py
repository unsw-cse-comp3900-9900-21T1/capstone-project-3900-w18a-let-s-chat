from django.urls import path

from . import views

urlpatterns = [
	#Leave as empty string for base url
	path('', views.store, name="store"),
    path('signup/', views.signup, name="signup"),
	path('login/', views.loginPage, name="login"),
    path('logout/', views.logoutUser, name="logout"),
    path('product/<slug:slug>/', views.product_page, name="product_page"),
	path('cart/', views.cart, name="cart"),
	path('checkout/', views.checkout, name="checkout"),
    path('purchase_history/', views.purchase_history, name="purchase_history"),
    path('wishList/', views.wishList, name="wishList"),
    path('watchList/', views.watchList, name="watchList"),
    path('user_profile/', views.userProfile, name="user_profile"),

]