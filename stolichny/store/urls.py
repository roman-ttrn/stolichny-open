from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.catalog, name='catalog'),
    path('catalog/<str:category_slug>/', views.catalog, name='catalog_certain'),
    path('cart/', views.cart, name='cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('add_to_cart/', views.add_to_cart, name='add_to_cart'),
    path('remove_from_cart/', views.remove_from_cart, name='remove_from_cart/'),
    path('product_page/<int:product_id>/', views.product_page, name='product_page'),
    path('user/', include('userapp.urls')),
    path('categories/', views.categories, name='categories'),
    path('get_cart_count/', views.get_cart_count, name='get_cart_count'),
    path('404/', views.custom_404_view, name='404'),
    path('api/search-products', views.search_products, name='search_products'),
    path('checkout/', views.checkout, name='checkout'),
    path('order_placing/', views.order_placing, name='order_placing'),
    path('order_sending/', views.order_sending, name='order_sending'),
    path('cancel_order/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('user_story_response/', views.user_story_response, name='user_story_response'),
    path('save_story_reaction/', views.save_story_reaction, name='save_story_reaction'),
    path('get_story_reaction/', views.get_story_reaction, name='get_story_reaction'),
    path('support/',views.support, name='support'),
    path('promo/', views.promo, name='promo'),
    path('api/get_delivery_price/', views.get_price, name='get_price'),
]