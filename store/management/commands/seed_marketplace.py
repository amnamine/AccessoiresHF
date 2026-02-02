"""
Seed marketplace: create seller/buyer users, user listings, and sample buy/sell orders.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import UserProfile
from store.models import Category, Product, Order, OrderItem


class Command(BaseCommand):
    help = 'Create marketplace users (sellers/buyers), their listings, and sample orders'

    def handle(self, *args, **options):
        # Ensure categories exist
        cats = {}
        for slug, name in [('watches', 'Watches'), ('jewelry', 'Jewelry'), ('bags', 'Bags'), ('sunglasses', 'Sunglasses'), ('belts', 'Belts')]:
            cat, _ = Category.objects.get_or_create(slug=slug, defaults={'name': name})
            cats[slug] = cat

        # Sellers
        john, _ = User.objects.get_or_create(username='john_seller', defaults={'email': 'john@example.com'})
        john.set_password('seller123')
        john.save()
        UserProfile.objects.get_or_create(user=john)
        jane, _ = User.objects.get_or_create(username='jane_seller', defaults={'email': 'jane@example.com'})
        jane.set_password('seller123')
        jane.save()
        UserProfile.objects.get_or_create(user=jane)

        # Buyers
        bob, _ = User.objects.get_or_create(username='bob_buyer', defaults={'email': 'bob@example.com'})
        bob.set_password('buyer123')
        bob.save()
        UserProfile.objects.get_or_create(user=bob)
        alice, _ = User.objects.get_or_create(username='alice_buyer', defaults={'email': 'alice@example.com'})
        alice.set_password('buyer123')
        alice.save()
        UserProfile.objects.get_or_create(user=alice)

        self.stdout.write(self.style.SUCCESS('Users: john_seller/seller123, jane_seller/seller123, bob_buyer/buyer123, alice_buyer/buyer123'))

        # John's listings (seller)
        john_listings = [
            ('Vintage Leather Watch', 'watches', 'M', 95.00, 'Classic vintage style watch.', 'vintage-leather-watch-john'),
            ('Silver Cuff Bracelet', 'jewelry', 'U', 42.00, 'Handcrafted silver cuff.', 'silver-cuff-bracelet-john'),
            ('Brown Leather Belt', 'belts', 'M', 38.00, 'Quality leather belt.', 'brown-leather-belt-john'),
        ]
        for name, cat_slug, gender, price, desc, slug in john_listings:
            p, created = Product.objects.get_or_create(slug=slug, defaults={
                'name': name, 'description': desc, 'price': price, 'stock': 10,
                'category': cats[cat_slug], 'gender': gender, 'seller': john,
            })
            if created:
                self.stdout.write(self.style.SUCCESS(f"  John's listing: {p.name}"))

        # Jane's listings (seller)
        jane_listings = [
            ('Silk Scarf Navy', 'jewelry', 'F', 55.00, 'Elegant silk scarf.', 'silk-scarf-navy-jane'),
            ('Gold Hoop Earrings', 'jewelry', 'F', 68.00, 'Classic gold hoops.', 'gold-hoop-earrings-jane'),
            ('Designer Sunglasses', 'sunglasses', 'F', 120.00, 'Trendy designer shades.', 'designer-sunglasses-jane'),
        ]
        for name, cat_slug, gender, price, desc, slug in jane_listings:
            p, created = Product.objects.get_or_create(slug=slug, defaults={
                'name': name, 'description': desc, 'price': price, 'stock': 8,
                'category': cats[cat_slug], 'gender': gender, 'seller': jane,
            })
            if created:
                self.stdout.write(self.style.SUCCESS(f"  Jane's listing: {p.name}"))

        # Bob buys from John (order) - idempotent
        john_watch = Product.objects.get(slug='vintage-leather-watch-john')
        order_bob, created_order_bob = Order.objects.get_or_create(
            user=bob, email='bob@example.com', total=95.00,
            defaults={
                'first_name': 'Bob', 'last_name': 'Buyer',
                'address': '123 Buyer St', 'city': 'New York', 'postal_code': '10001', 'country': 'USA', 'phone': '',
                'status': 'C',
            }
        )
        oi_bob, created_oi_bob = OrderItem.objects.get_or_create(order=order_bob, product=john_watch, defaults={
            'seller': john, 'quantity': 1, 'price': 95.00
        })
        if created_oi_bob:
            john_watch.stock = max(0, john_watch.stock - 1)
            john_watch.save(update_fields=['stock'])
            self.stdout.write(self.style.SUCCESS(f'Order: Bob bought {john_watch.name} from John'))

        # Alice buys from Jane (order) - idempotent
        jane_scarf = Product.objects.get(slug='silk-scarf-navy-jane')
        order_alice, _ = Order.objects.get_or_create(
            user=alice, email='alice@example.com', total=55.00,
            defaults={
                'first_name': 'Alice', 'last_name': 'Buyer',
                'address': '456 Buyer Ave', 'city': 'Boston', 'postal_code': '02101', 'country': 'USA', 'phone': '',
                'status': 'P',
            }
        )
        oi_alice, created_oi_alice = OrderItem.objects.get_or_create(order=order_alice, product=jane_scarf, defaults={
            'seller': jane, 'quantity': 1, 'price': 55.00
        })
        if created_oi_alice:
            jane_scarf.stock = max(0, jane_scarf.stock - 1)
            jane_scarf.save(update_fields=['stock'])
            self.stdout.write(self.style.SUCCESS(f'Order: Alice bought {jane_scarf.name} from Jane'))

        self.stdout.write(self.style.SUCCESS('Marketplace seed complete. Sellers have listings; buyers have orders; My Sales will show sold items.'))
