from django.contrib import admin
from .models import Category, Product, ProductImage, Order, OrderItem


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'seller', 'category', 'gender', 'price', 'stock', 'is_active', 'created_at']
    list_filter = ['category', 'gender', 'is_active']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline]
    list_editable = ['stock', 'is_active']
    raw_id_fields = ['seller']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'email', 'first_name', 'last_name', 'status', 'total', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['email', 'first_name', 'last_name']
    inlines = [OrderItemInline]
    list_editable = ['status']
