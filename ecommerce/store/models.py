from django.db import models
from django.contrib.auth.models import User
from taggit.managers import TaggableManager
from .util.generate_url_slugs import unique_slugify
from PIL import Image

import datetime

class Customer(models.Model):
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.CASCADE)
    nickname = models.CharField(max_length=200, null=True)
    email = models.EmailField(max_length=254)
    contactNo = models.CharField(max_length=200, null=True)
    image = models.ImageField(default='../images/user_icon.png', upload_to='../images')

    def __str__(self):
        return self.nickname

    def save(self):
        super().save()

        print(self.image.path)
        img = Image.open(self.image.path)

        if img.height > 300 or img.width > 300:
            output_size = (300, 300)
            img.thumbnail(output_size)
            img.save(self.image.path)


# class Tag(models.Model):
#     name = models.CharField(max_length=200)

#     def __str__(self):
#         return self.name

class Product(models.Model):
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=30, decimal_places=2)
    remaining_unit = models.IntegerField()
    sold_unit = models.IntegerField(default=0)
    isAnimal = models.BooleanField(default=False,null=True, blank=True)
    description = models.TextField(max_length=1000)
    image = models.ImageField(null=True, blank=True)
    warranty = models.CharField(max_length=200, null=True)
    delivery_period = models.DurationField()
    # seller = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    seller = models.CharField(max_length=200)
    tags = TaggableManager()
    slug_str = models.SlugField(blank=True)
    
    def save(self, **kwargs):
        unique_slugify(self, self.name, slug_field_name='slug_str')
        super(Product, self).save(**kwargs)

    def __str__(self):
        return self.name

    @property
    def imageURL(self):
        try:
            url = self.image.url
        except:
            url = ''
        return url

    @property
    def delivery_period_days_hours_str(self):
        secs = self.delivery_period.total_seconds()
        return f'{int(secs/86400)} days, {int((secs % 86400)/3600)} hours'

class Order(models.Model):
	customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
	date_ordered = models.DateTimeField(auto_now_add=True)
	complete = models.BooleanField(default=False)
	transaction_id = models.CharField(max_length=100, null=True)

	def __str__(self):
		return str(self.id)

	@property
	def get_cart_total(self):
		orderitems = self.orderitem_set.all()
		total = sum([item.get_total for item in orderitems])
		return total 

	@property
	def get_cart_items(self):
		orderitems = self.orderitem_set.all()
		total = sum([item.quantity for item in orderitems])
		return total 
        

class OrderItem(models.Model):
	product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
	order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
	quantity = models.IntegerField(default=0, null=True, blank=True)
	date_added = models.DateTimeField(auto_now_add=True)

	@property
	def get_total(self):
		total = self.product.price * self.quantity
		return total

class ShippingAddress(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
    recipient = models.CharField(max_length=200)
    address = models.CharField(max_length=200, null=False)
    city = models.CharField(max_length=200, null=False)
    state = models.CharField(max_length=200, null=False)
    postcode = models.CharField(max_length=200, null=False)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.address
