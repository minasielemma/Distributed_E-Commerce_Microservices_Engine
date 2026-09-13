import uuid
import random
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.core.management.base import BaseCommand
from catalog.models import (
    Product, ProductVariant, ProductImage, ProductAttribute,
    ProductAttributeValue, ProductReview, PriceDiscount
)

KADOSH_TENANT_ID = uuid.UUID('6cd2586e-1a03-4833-913f-598596f51732')

EXTRA_IMAGES_POOL = [
    'https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=800&auto=format&fit=crop&q=80',
    'https://images.unsplash.com/photo-1546868871-7041f2a55e12?w=800&auto=format&fit=crop&q=80',
    'https://images.unsplash.com/photo-1583394838336-acd977736f90?w=800&auto=format&fit=crop&q=80',
    'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&auto=format&fit=crop&q=80',
    'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=800&auto=format&fit=crop&q=80',
    'https://images.unsplash.com/photo-1560343090-f0409e92791a?w=800&auto=format&fit=crop&q=80',
    'https://images.unsplash.com/photo-1511556532299-8f662fc26c06?w=800&auto=format&fit=crop&q=80',
    'https://images.unsplash.com/photo-1584917865442-de89df76afd3?w=800&auto=format&fit=crop&q=80',
]

REVIEW_TEMPLATES = [
    {
        'user_name': 'Alexander Wright',
        'rating': 5,
        'title': 'Outstanding Quality!',
        'text': 'Exceeded my expectations in every way. High quality materials, fast shipping, and excellent packaging.'
    },
    {
        'user_name': 'Sophia Martinez',
        'rating': 5,
        'title': 'Best purchase this year',
        'text': 'I am extremely satisfied with this product. It works perfectly and feels super premium.'
    },
    {
        'user_name': 'Marcus Vance',
        'rating': 4,
        'title': 'Great value for money',
        'text': 'Solid product for the price point. Highly recommended if you are looking for reliable build quality.'
    },
    {
        'user_name': 'Emily Chen',
        'rating': 5,
        'title': 'Highly Recommended!',
        'text': 'Beautiful design and incredible performance. Will definitely be ordering from this seller again!'
    }
]


class Command(BaseCommand):
    help = 'Enriches all products for tenant kadosh with multi-variants, attribute values, image galleries, and customer reviews.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(f"Enriching Products for Tenant: {KADOSH_TENANT_ID}..."))

        # 1. Setup Base Attributes and Values
        color_attr, _ = ProductAttribute.objects.get_or_create(
            name='Color', tenant_id=None, defaults={'category': 'COLOR', 'display_order': 1}
        )
        size_attr, _ = ProductAttribute.objects.get_or_create(
            name='Size', tenant_id=None, defaults={'category': 'SIZE', 'display_order': 2}
        )

        black_val, _ = ProductAttributeValue.objects.get_or_create(attribute=color_attr, value='Black', defaults={'code': '#000000'})
        silver_val, _ = ProductAttributeValue.objects.get_or_create(attribute=color_attr, value='Silver', defaults={'code': '#C0C0C0'})
        blue_val, _ = ProductAttributeValue.objects.get_or_create(attribute=color_attr, value='Blue', defaults={'code': '#0000FF'})
        gold_val, _ = ProductAttributeValue.objects.get_or_create(attribute=color_attr, value='Gold', defaults={'code': '#FFD700'})

        size_m, _ = ProductAttributeValue.objects.get_or_create(attribute=size_attr, value='M', defaults={'code': 'M'})
        size_l, _ = ProductAttributeValue.objects.get_or_create(attribute=size_attr, value='L', defaults={'code': 'L'})
        size_xl, _ = ProductAttributeValue.objects.get_or_create(attribute=size_attr, value='XL', defaults={'code': 'XL'})

        variant_combos = [
            {'name_suffix': 'Standard Black / M', 'color': black_val, 'size': size_m, 'price_mult': Decimal('1.00'), 'stock': 35},
            {'name_suffix': 'Deluxe Silver / L', 'color': silver_val, 'size': size_l, 'price_mult': Decimal('1.15'), 'stock': 25},
            {'name_suffix': 'Pro Blue / XL', 'color': blue_val, 'size': size_xl, 'price_mult': Decimal('1.25'), 'stock': 40},
        ]

        products = Product.objects.filter(tenant_id=KADOSH_TENANT_ID)
        self.stdout.write(f"Found {products.count()} products to enrich.")

        now = timezone.now()
        discount_count = 0
        variant_count = 0
        review_count = 0
        image_count = 0

        for idx, prod in enumerate(products):
            # A) Enrich Images (Ensure 3 images per product)
            existing_imgs = list(prod.images.all())
            if len(existing_imgs) < 3:
                # Pick 2 extra images from pool
                extra_1 = EXTRA_IMAGES_POOL[idx % len(EXTRA_IMAGES_POOL)]
                extra_2 = EXTRA_IMAGES_POOL[(idx + 3) % len(EXTRA_IMAGES_POOL)]

                if len(existing_imgs) == 1:
                    ProductImage.objects.create(
                        product=prod, tenant_id=KADOSH_TENANT_ID, image_url=extra_1, alt_text=f"{prod.name} View 2", is_primary=False, display_order=2
                    )
                    ProductImage.objects.create(
                        product=prod, tenant_id=KADOSH_TENANT_ID, image_url=extra_2, alt_text=f"{prod.name} View 3", is_primary=False, display_order=3
                    )
                    image_count += 2

            # B) Enrich Variants & Link Attribute Values
            current_variants = list(prod.variants.all())
            base_price = prod.base_price or Decimal('49.99')

            # Create 3 detailed variants if only 1 exists
            for v_idx, combo in enumerate(variant_combos):
                v_sku = f"{prod.sku}-V{v_idx + 1}"
                var_obj, created = ProductVariant.objects.get_or_create(
                    product=prod,
                    sku=v_sku,
                    defaults={
                        'tenant_id': KADOSH_TENANT_ID,
                        'price': round(base_price * combo['price_mult'], 2),
                        'stock': combo['stock'],
                        'is_active': True
                    }
                )
                if created:
                    variant_count += 1
                
                # Attach attribute values (Color + Size)
                var_obj.attribute_values.add(combo['color'], combo['size'])

            # Clean up initial temporary single variant if present
            for old_v in current_variants:
                if old_v.sku.endswith('-VAR1') and prod.variants.count() > 3:
                    old_v.delete()

            # C) Enrich Customer Reviews
            existing_reviews = prod.reviews.count()
            if existing_reviews < 2:
                # Create 2-3 reviews per product
                num_reviews = 2 + (idx % 2)
                for r_idx in range(num_reviews):
                    t = REVIEW_TEMPLATES[(idx + r_idx) % len(REVIEW_TEMPLATES)]
                    u_id = uuid.uuid5(KADOSH_TENANT_ID, f"{prod.id}-user-{r_idx}")
                    ProductReview.objects.get_or_create(
                        product=prod,
                        user_id=u_id,
                        defaults={
                            'tenant_id': KADOSH_TENANT_ID,
                            'user_name': t['user_name'],
                            'rating': t['rating'],
                            'title': t['title'],
                            'review_text': t['text'],
                            'is_verified_purchase': True
                        }
                    )
                    review_count += 1

            # D) Apply Price Discounts (25% of products get active 15% discount)
            if idx % 4 == 0:
                PriceDiscount.objects.get_or_create(
                    product=prod,
                    tenant_id=KADOSH_TENANT_ID,
                    title='Special Seasonal Sale 15% OFF',
                    defaults={
                        'discount_type': 'PERCENTAGE',
                        'discount_value': Decimal('15.00'),
                        'start_time': now - timedelta(days=5),
                        'end_time': now + timedelta(days=25),
                        'is_active': True,
                        'priority': 10
                    }
                )
                discount_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Successfully enriched products!\n"
            f"- Added {image_count} gallery images\n"
            f"- Created/configured {variant_count} multi-attribute variants\n"
            f"- Created {review_count} customer reviews\n"
            f"- Configured {discount_count} active price discounts."
        ))
