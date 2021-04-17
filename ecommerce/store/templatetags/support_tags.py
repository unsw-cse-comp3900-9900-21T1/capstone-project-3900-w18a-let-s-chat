from django import template
from ..models import Customer

register = template.Library()

@register.simple_tag
def check_exist_tag(customer, product):
    if isinstance(customer, Customer):
        wishlist = customer.wishlist
        return customer.wishlist.check_exist(wishlist, product)
    else:
        return False