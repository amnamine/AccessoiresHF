from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.admin.views.decorators import staff_member_required
from .models import Product, Category, Order, OrderItem
from .cart import cart_items, cart_total, cart_add, cart_remove, cart_update, cart_clear
from .forms import CheckoutForm


def home(request):
    """Home page with featured products."""
    featured = Product.objects.filter(is_active=True)[:8]
    categories = Category.objects.all()[:6]
    return render(request, 'store/home.html', {
        'featured': featured,
        'categories': categories,
    })


def shop(request):
    """Shop listing with category and gender filters."""
    qs = Product.objects.filter(is_active=True)
    category_slug = request.GET.get('category')
    gender = request.GET.get('gender')
    q = request.GET.get('q', '').strip()

    if category_slug:
        qs = qs.filter(category__slug=category_slug)
    if gender and gender in ('M', 'F', 'U'):
        qs = qs.filter(gender=gender)
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(description__icontains=q))

    paginator = Paginator(qs, 12)
    page = request.GET.get('page', 1)
    products = paginator.get_page(page)
    categories = Category.objects.all()

    return render(request, 'store/shop.html', {
        'products': products,
        'categories': categories,
        'selected_category': category_slug,
        'selected_gender': gender,
        'search_q': q,
    })


def product_detail(request, slug):
    """Product detail page."""
    product = get_object_or_404(Product, slug=slug, is_active=True)
    related = Product.objects.filter(category=product.category, is_active=True).exclude(id=product.id)[:4]
    return render(request, 'store/product_detail.html', {
        'product': product,
        'related': related,
    })


def cart_view(request):
    """Cart page."""
    items = cart_items(request)
    total = cart_total(request)
    return render(request, 'store/cart.html', {'cart_items': items, 'cart_total': total})


def cart_add_view(request, product_id):
    """Add to cart (POST)."""
    if request.method != 'POST':
        return redirect('store:shop')
    quantity = int(request.POST.get('quantity', 1))
    if cart_add(request, product_id, quantity):
        messages.success(request, 'Item added to cart.')
    else:
        messages.error(request, 'Product not found or out of stock.')
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or request.build_absolute_uri('/shop/')
    return redirect(next_url)


def cart_remove_view(request, product_id):
    """Remove from cart."""
    cart_remove(request, product_id)
    messages.info(request, 'Item removed from cart.')
    return redirect('store:cart')


def cart_update_view(request, product_id):
    """Update quantity in cart (POST)."""
    if request.method != 'POST':
        return redirect('store:cart')
    quantity = int(request.POST.get('quantity', 0))
    cart_update(request, product_id, quantity)
    messages.info(request, 'Cart updated.')
    return redirect('store:cart')


def checkout(request):
    """Checkout: show form and place order."""
    items = cart_items(request)
    if not items:
        messages.warning(request, 'Your cart is empty.')
        return redirect('store:shop')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            if request.user.is_authenticated:
                order.user = request.user
                order.email = order.email or request.user.email or request.user.username
            order.total = cart_total(request)
            order.save()
            for item in items:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    quantity=item['quantity'],
                    price=item['price'],
                )
                item['product'].stock -= item['quantity']
                item['product'].save(update_fields=['stock'])
            cart_clear(request)
            messages.success(request, 'Order placed successfully!')
            return redirect('store:order_confirmation', order_id=order.id)
        # form invalid: fall through to render with form errors
    else:
        initial = {}
        if request.user.is_authenticated:
            initial['email'] = request.user.email or ''
            initial['first_name'] = request.user.first_name or ''
            initial['last_name'] = request.user.last_name or ''
            if hasattr(request.user, 'profile') and request.user.profile:
                p = request.user.profile
                initial['phone'] = p.phone or ''
                initial['address'] = p.default_address or ''
                initial['city'] = p.default_city or ''
                initial['postal_code'] = p.default_postal_code or ''
                initial['country'] = p.default_country or ''
        form = CheckoutForm(initial=initial)

    total = cart_total(request)
    return render(request, 'store/checkout.html', {'form': form, 'cart_items': items, 'cart_total': total})


def order_confirmation(request, order_id):
    """Order confirmation page."""
    order = get_object_or_404(Order, id=order_id)
    if request.user.is_authenticated and request.user.is_staff:
        pass  # staff can view any order
    elif request.user.is_authenticated and order.user != request.user:
        messages.error(request, 'Order not found.')
        return redirect('store:home')
    elif not request.user.is_authenticated and order.user_id:
        messages.error(request, 'Order not found.')
        return redirect('store:home')
    return render(request, 'store/order_confirmation.html', {'order': order})


# --- Admin dashboard (staff only) ---

@staff_member_required
def admin_dashboard(request):
    """Admin dashboard with stats."""
    from django.contrib.auth import get_user_model

    User = get_user_model()
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='P').count()
    total_users = User.objects.filter(is_staff=False).count()
    low_stock_products = Product.objects.filter(stock__lte=5, stock__gt=0).count()
    out_of_stock = Product.objects.filter(stock=0).count()
    recent_orders = Order.objects.all()[:10]

    return render(request, 'store/admin/dashboard.html', {
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'total_users': total_users,
        'low_stock_products': low_stock_products,
        'out_of_stock': out_of_stock,
        'recent_orders': recent_orders,
    })
