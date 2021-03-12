from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
	#Leave as empty string for base url
	path('', views.store, name="store"),
    path('signup/', views.signup, name="signup"),
    path('signup_success/', views.signup_success, name="signup_success"),
	path('login/', views.loginPage, name="login"),
    path('logout/', views.logoutUser, name="logout"),
    path('product_description/', views.product_description, name="product_description"),
	path('cart/', views.cart, name="cart"),
	path('checkout/', views.checkout, name="checkout"),
    path('purchase_history/', views.purchase_history, name="purchase_history"),
    path('wishList/', views.wishList, name="wishList"),
    path('watchList/', views.watchList, name="watchList"),
    path('user_profile/', views.userProfile, name="user_profile"),

    path('reset_password/',
        auth_views.PasswordResetView.as_view(template_name="store/password_reset.html"),
        name="reset_password"),

    path('reset_password_sent/', 
        auth_views.PasswordResetDoneView.as_view(template_name="store/password_reset_sent.html"), 
        name="password_reset_done"),

    path('reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(template_name="store/password_reset_form.html"), 
        name="password_reset_confirm"),

    path('reset_password_complete/', 
        auth_views.PasswordResetCompleteView.as_view(template_name="store/password_reset_done.html"), 
        name="password_reset_complete"),

]