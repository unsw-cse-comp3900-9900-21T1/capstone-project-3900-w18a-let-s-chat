from django.contrib import admin

from .models import *

admin.site.register(Customer)
admin.site.register(Product)
# admin.site.register(Tag)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(ShippingAddress)
admin.site.register(ProductViewCount)
admin.site.register(ProductReview)
admin.site.register(ReviewReact)
admin.site.register(Bidder)
admin.site.register(Wishlist)