from django import template

register = template.Library()

@register.simple_tag
def check_exist_tag(customer, product):
    wishlist = customer.wishlist
    return customer.wishlist.check_exist(wishlist, product)