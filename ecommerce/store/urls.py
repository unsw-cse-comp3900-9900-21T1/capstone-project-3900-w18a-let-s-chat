from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
	#Leave as empty string for base url
	path('', views.store, name="store"),
    path('signup/', views.signup, name="signup"),
    path('signup_success/', views.signup_success, name="signup_success"),
	path('login/', views.loginPage, name="login"),
    path('logout/', views.logoutUser, name="logout"),
    path('product/<slug:slug>/', views.product_page, name="product_page"),
	path('cart/', views.cart, name="cart"),
	path('checkout/', views.checkout, name="checkout"),
    path('purchase_history/', views.purchase_history, name="purchase_history"),
    path('wishlist/', views.wishlist, name="wishlist"),
    path('user_profile/', views.userProfile, name="user_profile"),
    path('search_result/', views.searchResult, name="search_result"),
    path('process_order/', views.processOrder, name="process_order"),
    path('new_product/', views.new_product, name='new_product'),
    path('my_listings/', views.my_listings, name='my_listings'),
    path('view_orders/<slug:slug>/', views.view_orders, name="view_orders"),
    path('edit_listing/<slug:slug>/', views.edit_listing, name="edit_listing"),
    path('toggle_unlist/', views.toggle_unlist, name='toggle_unlist'),
    path('new_review/', views.post_new_review, name='new_review'),
    path('delete_review/', views.delete_review, name='delete_review'),
    path('edit_review/', views.edit_review, name='edit_review'),
    path('toggle_review_react/', views.toggle_review_react, name='toggle_review_react'),

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

    
    path('update_item/', views.updateItem, name="update_item"),
    path('add_multiple/', views.add_multiple, name="add_multiple"),
    path('restore/', views.restore, name="restore"),
    # path('chat_index/', views.index_view, name='index'),
    # path('chat/', views.chat_view, name="chat_view"),
    path('webhook/', views.webhook, name="webhook"),
    path('add_bid/', views.add_bid, name="add_bid"),
    path('add_wishlist/', views.add_wishlist, name="add_wishlist"),
    path('remove_wishlist/', views.remove_wishlist, name="remove_wishlist"),
]
