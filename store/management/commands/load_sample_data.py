from django.core.management.base import BaseCommand
from store.models import Category, Product


class Command(BaseCommand):
    help = 'Load sample categories and products'

    def handle(self, *args, **options):
        categories_data = [
            {'name': 'Watches', 'slug': 'watches', 'description': 'Elegant timepieces for men and women.'},
            {'name': 'Jewelry', 'slug': 'jewelry', 'description': 'Rings, bracelets, necklaces and more.'},
            {'name': 'Bags', 'slug': 'bags', 'description': 'Handbags, clutches and backpacks.'},
            {'name': 'Sunglasses', 'slug': 'sunglasses', 'description': 'Stylish eyewear for every occasion.'},
            {'name': 'Belts', 'slug': 'belts', 'description': 'Belts and waist accessories.'},
        ]
        for data in categories_data:
            cat, created = Category.objects.get_or_create(slug=data['slug'], defaults=data)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created category: {cat.name}'))

        products_data = [
            ('Classic Leather Watch', 'watches', 'M', 129.99, 'Timeless leather strap watch for men.'),
            ('Rose Gold Bracelet', 'jewelry', 'F', 89.99, 'Delicate rose gold bracelet.'),
            ('Minimalist Silver Ring', 'jewelry', 'U', 45.00, 'Simple silver band, unisex.'),
            ('Leather Crossbody Bag', 'bags', 'F', 159.99, 'Compact leather crossbody.'),
            ('Aviator Sunglasses', 'sunglasses', 'U', 79.99, 'Classic aviator style.'),
            ('Classic Belt Brown', 'belts', 'M', 59.99, 'Genuine leather belt.'),
            ('Pearl Stud Earrings', 'jewelry', 'F', 65.00, 'Elegant pearl studs.'),
            ('Smart Watch Black', 'watches', 'U', 199.99, 'Modern smartwatch with fitness tracking.'),
        ]
        for name, cat_slug, gender, price, desc in products_data:
            cat = Category.objects.get(slug=cat_slug)
            slug = name.lower().replace(' ', '-').replace("'", '')
            product, created = Product.objects.get_or_create(
                slug=slug,
                defaults={
                    'name': name,
                    'description': desc,
                    'price': price,
                    'stock': 25,
                    'category': cat,
                    'gender': gender,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created product: {product.name}'))

        self.stdout.write(self.style.SUCCESS('Sample data loaded.'))
