from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse
from django.utils.text import slugify
from .models import Product, Category, Order, OrderItem
from .cart import cart_items, cart_total, cart_add, cart_remove, cart_update, cart_clear
from .forms import CheckoutForm, ProductForm


def home(request):
    """Home page with featured products split by Men / Women."""
    categories = Category.objects.all()[:6]
    featured_men = Product.objects.filter(is_active=True, gender='M')[:8]
    featured_women = Product.objects.filter(is_active=True, gender='F')[:8]
    featured_unisex = Product.objects.filter(is_active=True, gender='U')[:4]
    return render(request, 'store/home.html', {
        'categories': categories,
        'featured_men': featured_men,
        'featured_women': featured_women,
        'featured_unisex': featured_unisex,
    })


def shop(request, gender=None):
    """Shop listing with category and gender filters. gender can come from URL (Men/Women) or GET."""
    qs = Product.objects.filter(is_active=True)
    category_slug = request.GET.get('category')
    gender = gender or request.GET.get('gender')
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


@login_required
def cart_view(request):
    """Cart page. Login required to buy (add to cart, checkout)."""
    items = cart_items(request)
    total = cart_total(request)
    return render(request, 'store/cart.html', {'cart_items': items, 'cart_total': total})


@login_required
def cart_add_view(request, product_id):
    """Add to cart (POST). Login required to buy. Cannot add your own listing."""
    if request.method != 'POST':
        return redirect('store:shop')
    try:
        product = Product.objects.get(pk=product_id, is_active=True)
        if product.seller == request.user:
            messages.error(request, "You cannot buy your own listing.")
            next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or request.build_absolute_uri('/shop/')
            return redirect(next_url)
    except Product.DoesNotExist:
        pass
    quantity = int(request.POST.get('quantity', 1))
    if cart_add(request, product_id, quantity):
        messages.success(request, 'Item added to cart.')
    else:
        messages.error(request, 'Product not found or out of stock.')
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or request.build_absolute_uri('/shop/')
    return redirect(next_url)


@login_required
def cart_remove_view(request, product_id):
    """Remove from cart."""
    cart_remove(request, product_id)
    messages.info(request, 'Item removed from cart.')
    return redirect('store:cart')


@login_required
def cart_update_view(request, product_id):
    """Update quantity in cart (POST)."""
    if request.method != 'POST':
        return redirect('store:cart')
    quantity = int(request.POST.get('quantity', 0))
    cart_update(request, product_id, quantity)
    messages.info(request, 'Cart updated.')
    return redirect('store:cart')


@login_required
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
            order.user = request.user
            order.email = order.email or request.user.email or request.user.username
            order.total = cart_total(request)
            order.save()
            for item in items:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    seller=item['product'].seller,
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
        initial = {
            'email': request.user.email or '',
            'first_name': request.user.first_name or '',
            'last_name': request.user.last_name or '',
        }
        if hasattr(request.user, 'profile') and request.user.profile:
            p = request.user.profile
            initial.update({'phone': p.phone or '', 'address': p.default_address or '', 'city': p.default_city or '', 'postal_code': p.default_postal_code or '', 'country': p.default_country or ''})
        form = CheckoutForm(initial=initial)

    total = cart_total(request)
    return render(request, 'store/checkout.html', {'form': form, 'cart_items': items, 'cart_total': total})


# --- Seller: my listings, add/edit/delete, my sales ---

@login_required
def my_listings(request):
    """List products the current user is selling."""
    products = Product.objects.filter(seller=request.user).order_by('-created_at')
    return render(request, 'store/seller/my_listings.html', {'products': products})


@login_required
def add_listing(request):
    """Create a new listing (product) for the current user."""
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.seller = request.user
            base_slug = slugify(product.name)[:180] or 'item'
            slug = base_slug
            n = 0
            while Product.objects.filter(slug=slug).exists():
                n += 1
                slug = f'{base_slug}-{n}'
            product.slug = slug
            product.save()
            messages.success(request, 'Listing created.')
            return redirect('store:my_listings')
    else:
        form = ProductForm()
    return render(request, 'store/seller/add_listing.html', {'form': form})


@login_required
def edit_listing(request, pk):
    """Edit a listing. Only owner or staff."""
    product = get_object_or_404(Product, pk=pk)
    if product.seller != request.user and not request.user.is_staff:
        messages.error(request, 'You cannot edit this listing.')
        return redirect('store:my_listings')
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Listing updated.')
            return redirect('store:my_listings')
    else:
        form = ProductForm(instance=product)
    return render(request, 'store/seller/edit_listing.html', {'form': form, 'product': product})


@login_required
def delete_listing(request, pk):
    """Delete a listing. Only owner or staff."""
    product = get_object_or_404(Product, pk=pk)
    if product.seller != request.user and not request.user.is_staff:
        messages.error(request, 'You cannot delete this listing.')
        return redirect('store:my_listings')
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Listing deleted.')
        return redirect('store:my_listings')
    return render(request, 'store/seller/delete_listing_confirm.html', {'product': product})


@login_required
def my_sales(request):
    """List order items the current user sold (seller side)."""
    items = OrderItem.objects.filter(seller=request.user).select_related('order', 'product').order_by('-order__created_at')
    return render(request, 'store/seller/my_sales.html', {'sold_items': items})


def order_confirmation(request, order_id):
    """Order confirmation page. Viewable by buyer (order.user), staff, or any seller in this order."""
    order = get_object_or_404(Order, id=order_id)
    if not request.user.is_authenticated:
        messages.warning(request, 'Please log in to view your order.')
        return redirect(reverse('accounts:login') + '?next=' + request.build_absolute_uri())
    can_view = (
        request.user.is_staff
        or order.user == request.user
        or order.items.filter(seller=request.user).exists()
    )
    if not can_view:
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
