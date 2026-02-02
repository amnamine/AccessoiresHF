from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    path('', views.home, name='home'),
    path('shop/', views.shop, name='shop'),
    path('shop/men/', views.shop, {'gender': 'M'}, name='shop_men'),
    path('shop/women/', views.shop, {'gender': 'F'}, name='shop_women'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:product_id>/', views.cart_add_view, name='cart_add'),
    path('cart/remove/<int:product_id>/', views.cart_remove_view, name='cart_remove'),
    path('cart/update/<int:product_id>/', views.cart_update_view, name='cart_update'),
    path('checkout/', views.checkout, name='checkout'),
    path('order/<int:order_id>/confirmation/', views.order_confirmation, name='order_confirmation'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    # Seller: my listings, add/edit/delete, my sales
    path('my-listings/', views.my_listings, name='my_listings'),
    path('my-listings/add/', views.add_listing, name='add_listing'),
    path('my-listings/<int:pk>/edit/', views.edit_listing, name='edit_listing'),
    path('my-listings/<int:pk>/delete/', views.delete_listing, name='delete_listing'),
    path('my-sales/', views.my_sales, name='my_sales'),
]
