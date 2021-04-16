from __future__ import unicode_literals
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from taggit.managers import TaggableManager
from .util.generate_url_slugs import unique_slugify
from PIL import Image

import datetime 
SELLING_CHOICES = [
    ('sale', 'Sales'),
    ('auction', 'Auctions')
]

no_image_url = '/images/no-image.jpg'

class Customer(models.Model):
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.CASCADE)
    nickname = models.CharField(max_length=200, null=True)
    email = models.EmailField(max_length=254)
    contactNo = models.CharField(max_length=200, null=True)
    image = models.ImageField(default='../images/user_icon.png', upload_to='../images')
    trusted = models.BooleanField(default=False)

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


class Product(models.Model):
    name = models.CharField(max_length=200)
    selling_type = models.CharField(max_length=10, choices=SELLING_CHOICES, default='sale')
    price = models.DecimalField(max_digits=30, decimal_places=2)
    starting_bid = models.DecimalField(max_digits=30, decimal_places=2, default=0)
    end_date = models.DateTimeField(default=timezone.now, blank=True, null=True)
    highest_bidder = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True, related_name='highest_bidder')
    remaining_unit = models.IntegerField()
    sold_unit = models.IntegerField(default=0)
    isAnimal = models.BooleanField(default=False,null=True, blank=True)
    description = models.TextField(max_length=1000)
    image = models.ImageField(null=True, blank=True)
    warranty = models.CharField(max_length=200, null=True)
    delivery_period = models.DurationField()
    seller = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True)
    tags = TaggableManager()
    estimated_date = models.DateTimeField(editable=False, blank=True, null=True)
    slug_str = models.SlugField(blank=True)
    is_active = models.BooleanField(default=True)
    
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
            url = no_image_url
        return url

    @property
    def delivery_period_days_hours_str(self):
        secs = self.delivery_period.total_seconds()
        return f'{int(secs/86400)} days, {int((secs % 86400)/3600)} hours'
    
    @property
    def avg_rating(self):
        if self.reviews.count() == 0:
            return 2.5
        else:
            return float(self.reviews.aggregate(models.Avg('rating'))['rating__avg'])
    
    @property
    def bidder_count(self):
        return self.bidder.count()

class Bidder(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=30, decimal_places=2)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='bidder')

    class Meta:
        # order_with_respect_to = 'product'
        ordering = ['id']

    def __str__(self):
        return self.name

class ProductReview(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    author = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)
    date_posted = models.DateTimeField(auto_now_add=True)
    edited = models.BooleanField(default=False)

    rating = models.PositiveIntegerField(blank=False)
    text = models.TextField(max_length=1000, blank=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['product', 'author'], name='User can only leave one review per product')
        ]

    @property
    def score(self):
        return self.reacts.filter(liked=True).count() - self.reacts.filter(liked=False).count()
    
    @property
    def timestamp(self):
        return self.date_posted.timestamp()
    
    def __str__(self):
        return f'{self.product} review by {self.author} ({self.rating} stars)'
    
class ReviewReact(models.Model):
    review = models.ForeignKey(ProductReview, on_delete=models.CASCADE, related_name='reacts')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)

    liked = models.BooleanField(default=True, blank=False)

    def __str__(self):
        return f"{self.customer} {'liked' if self.liked else 'disliked'} {self.review.author}'s review of {self.review.product}"

class Order(models.Model):
	customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
	date_ordered = models.DateTimeField(editable=False, blank=True, null=True)
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
		if self.product.selling_type == "sale":
			total = self.product.price * self.quantity
		else:
			total = self.product.starting_bid
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

class ProductViewCount(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    count = models.PositiveIntegerField(default=0)
    last_viewing = models.DateTimeField(auto_now=True)

    @staticmethod
    def log(customer, product):
        ''' 
        Log the viewing of a product by a customer.
        Returns the number of times the given product has been viewed by the customer
        '''

        view_counter, created = ProductViewCount.objects.get_or_create(
                                    customer=customer,
                                    product=product)
        view_counter.count += 1
        view_counter.save()

        return view_counter.count

    def __str__(self):
        return f'Customer: {self.customer}, Product: {self.product}, Count: {self.count}'

