def cart_count(request):
    """Add cart item count to template context."""
    count = 0
    if request.session.get('cart'):
        for item in request.session['cart'].values():
            count += item.get('quantity', 0)
    return {'cart_count': count}


def categories_nav(request):
    """Add categories for navigation."""
    from .models import Category
    categories = Category.objects.all()[:10]
    return {'nav_categories': categories}
