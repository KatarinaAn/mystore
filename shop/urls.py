
from django.urls import path, re_path

from shop import views

urlpatterns = [
    path('', views.index, name='index'),
    path('delivery', views.delivery, name='delivery'),
    path('contacts', views.contacts, name='contacts'),
    re_path(r'^section/(?P<id>\d+)$', views.section, name='section'),
    re_path(r'^product/(?P<pk>\d+)$', views.ProductDetailView.as_view(), name='product'),
    path('search', views.search, name='search'),
    path('cart', views.cart, name='cart'),
    path('order', views.order, name='order'),
    path('addorder', views.addorder, name='addorder'),
]
