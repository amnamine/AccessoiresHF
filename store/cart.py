"""Cart helpers using session."""
from decimal import Decimal
from .models import Product


def get_cart(request):
    """Return cart dict from session. Format: {product_id: {'quantity': int, 'price': str}}."""
    return request.session.get('cart', {})


def cart_add(request, product_id, quantity=1):
    """Add or update item in cart."""
    cart = get_cart(request).copy()
    try:
        product = Product.objects.get(pk=product_id, is_active=True)
    except Product.DoesNotExist:
        return False
    q = cart.get(str(product_id), {}).get('quantity', 0) + quantity
    if q > product.stock:
        q = product.stock
    if q <= 0:
        cart.pop(str(product_id), None)
    else:
        cart[str(product_id)] = {'quantity': q, 'price': str(product.price)}
    request.session['cart'] = cart
    request.session.modified = True
    return True


def cart_remove(request, product_id):
    """Remove item from cart."""
    cart = get_cart(request).copy()
    cart.pop(str(product_id), None)
    request.session['cart'] = cart
    request.session.modified = True


def cart_update(request, product_id, quantity):
    """Set quantity for item. Remove if quantity <= 0."""
    if quantity <= 0:
        cart_remove(request, product_id)
        return True
    return cart_add(request, product_id, quantity - (get_cart(request).get(str(product_id), {}).get('quantity', 0)))


def cart_clear(request):
    """Clear entire cart."""
    request.session['cart'] = {}
    request.session.modified = True


def cart_items(request):
    """Return list of (product, quantity, line_total) for template."""
    cart = get_cart(request)
    if not cart:
        return []
    product_ids = list(cart.keys())
    products = {str(p.id): p for p in Product.objects.filter(id__in=product_ids, is_active=True)}
    result = []
    for pid, data in cart.items():
        if pid not in products:
            continue
        product = products[pid]
        qty = data.get('quantity', 0)
        if qty > product.stock:
            qty = product.stock
        price = Decimal(data.get('price', product.price))
        result.append({'product': product, 'quantity': qty, 'price': price, 'subtotal': qty * price})
    return result


def cart_total(request):
    """Return total amount for cart."""
    return sum(item['subtotal'] for item in cart_items(request))


def cart_count(request):
    """Return total number of items in cart."""
    return sum(item['quantity'] for item in cart_items(request))
