import math

from .models import Product, Customer, ProductViewCount, Order, OrderItem

class Recommender():
    '''
    Profile a customer using their viewing and purchase history and find the
    products most suited to them
    - Leave customer param as None if working with guest user
    '''

    def __init__(self, customer=None):
        self.customer = customer
        self.profile_dict = self.get_customer_profile()

    def get_customer_profile(self, purchase_weight=2.0):
        '''
        Generate the customers's profile using their viewing and purchase history
        '''

        # Return empty profile dict for guest user
        if not self.customer:
            return dict()

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
            if not order_item.product is None: # Check product not deleted
                for tag in order_item.product.tags.names():
                    profile[tag] = float(profile.get(tag, 0) + (1 * purchase_weight))

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

  


    def calculate_score(self, product, max_rating_weight=0.3, max_reviews=5, max_rating=5):
        '''
        Calculate the final recommender score of a product
        
        Score is the weighted average of the product's similarity and its review score, with
        the review score weighted more heavily if there are more reviews
        
        Eg. if a product has no reviews the score will be entirely based on the similarity score,
        while if a product has 'max_reviews' reviews, the review score will make up 'max_rating_weight'
        of the final score.
        
        If a user is a guest, and thus similarity cannot be found, only the product's review score will be used
        '''


        # Use only product rating if user is guest
        if not self.customer:
            return product.avg_rating / max_rating

        # Calculate weighting of reviews versus similarity
        n_reviews_clamped = max(0, min(product.reviews.count(), max_reviews))
        max_reviews_fraction = n_reviews_clamped / float(max_reviews)
        rating_weight = max_rating_weight * max_reviews_fraction
        similarity_weight = 1 - rating_weight

        return (self.calculate_similarity(product) * similarity_weight) + ((product.avg_rating / max_rating) * rating_weight)

    
    def get_recommended_products(self, max_results=1000):
        '''
        Return a list of the products most similar to the user's profile, that still have units left
        '''

        products = Product.objects.filter(remaining_unit__gt=0, is_active=True)
        
        products = sorted(products, key=lambda p: self.calculate_score(p), reverse=True)
        return products[:max_results]
