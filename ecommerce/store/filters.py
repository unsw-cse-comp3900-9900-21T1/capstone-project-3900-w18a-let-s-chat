import django_filters

from .models import *

class ProductFilter(django_filters.FilterSet):
	price__gt = django_filters.NumberFilter(field_name='price', lookup_expr='gt')
	price__lt = django_filters.NumberFilter(field_name='price', lookup_expr='lt')

	class Meta:
		model = Product
		fields = ['selling_type','isAnimal']