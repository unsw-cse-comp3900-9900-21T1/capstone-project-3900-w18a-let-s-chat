from django.contrib import admin

<<<<<<< HEAD
# Register your models here.
=======
from .models import *

admin.site.register(Customer)
admin.site.register(Product)
# admin.site.register(Tag)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(ShippingAddress)
>>>>>>> data_structure
