import math

from .models import Product, Customer, ProductViewCount, Order, OrderItem

class Recommender():
    '''
    Profile a customer using their viewing and purchase history and find the
    products most suited to them
    '''

    customer = None
    profile_dict = None

    def __init__(self, customer):
        self.customer = customer
        self.profile_dict = self.get_customer_profile()

    def get_customer_profile(self, purchase_weighting=2.0):
        '''
        Generate the customers's profile using their viewing and purchase history
        '''

        # Add to profile based on viewed items
        viewed = ProductViewCount.objects.filter(customer=self.customer)
        profile = dict()
        for item in viewed:
            for tag in item.product.tags.names():
                profile[tag] = float(profile.get(tag, 0) + item.count)

        # Add to profile based on purchases.
        orders = Order.objects.filter(customer=self.customer, complete=True)
        purchases = OrderItem.objects.filter(order__in=orders)
        for order_item in purchases:
            for tag in order_item.product.tags.names():
                profile[tag] = float(profile.get(tag, 0) + (1 * purchase_weighting))

        # print('User profile:', profile)
        return profile

    def calculate_similarity(self, product):
        '''
        Return the similarity between the customer's profile and a product,
        using the cosine similarity of product tags
        '''

        product_dict = {tag: 1 for tag in product.tags.names()}

        # Return zero similarity if either user or product has no tags (eg. new users)
        if all(count==0 for count in product_dict.values()) or all(count==0 for count in self.profile_dict.values()):
            return 0.0

        # Find cosine similarity between two dicts
        numerator = 0.0
        denom_a = 0.0
        for tag, count in product_dict.items():
            numerator += count * self.profile_dict.get(tag, 0)
            denom_a += count ** 2
        denom_b = 0.0
        for count in self.profile_dict.values():
            denom_b += count ** 2
        
        return float(numerator) / math.sqrt(denom_a*denom_b)

    
    def get_recommended_products(self, max_results=100):
        '''
        Return a list of the products most similar to the user's profile, that still have units left
        '''

        products = Product.objects.filter(remaining_unit__gt=0, is_active=True)
        products = sorted(products, key=lambda p: self.calculate_similarity(p), reverse=True)
        return products[:max_results]
