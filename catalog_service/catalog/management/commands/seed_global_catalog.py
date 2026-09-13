from django.core.management.base import BaseCommand
from catalog.models import Category, ProductAttribute, ProductAttributeValue


class Command(BaseCommand):
    help = 'Seeds global standard e-commerce taxonomy (categories & attributes) shared platform-wide.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting Global Catalog Seeding..."))

        # --- 1. GLOBAL CATEGORIES & SUBCATEGORIES ---
        global_categories_data = [
            {
                'name': 'Electronics & Gadgets',
                'slug': 'electronics-gadgets',
                'subcategories': [
                    {'name': 'Smartphones & Mobile Devices', 'slug': 'smartphones-mobile-devices'},
                    {'name': 'Laptops & Computers', 'slug': 'laptops-computers'},
                    {'name': 'Audio & Headphones', 'slug': 'audio-headphones'},
                    {'name': 'Cameras & Photography', 'slug': 'cameras-photography'},
                    {'name': 'Wearable Technology', 'slug': 'wearable-technology'},
                    {'name': 'Electronics Accessories', 'slug': 'electronics-accessories'},
                ]
            },
            {
                'name': 'Clothing & Fashion',
                'slug': 'clothing-fashion',
                'subcategories': [
                    {'name': "Men's Clothing", 'slug': 'mens-clothing'},
                    {'name': "Women's Clothing", 'slug': 'womens-clothing'},
                    {'name': 'Kids & Baby Clothing', 'slug': 'kids-baby-clothing'},
                    {'name': 'Shoes & Footwear', 'slug': 'shoes-footwear'},
                    {'name': 'Bags & Luggage', 'slug': 'bags-luggage'},
                    {'name': 'Jewelry & Watches', 'slug': 'jewelry-watches'},
                ]
            },
            {
                'name': 'Home, Kitchen & Living',
                'slug': 'home-kitchen-living',
                'subcategories': [
                    {'name': 'Furniture', 'slug': 'furniture'},
                    {'name': 'Home Decor', 'slug': 'home-decor'},
                    {'name': 'Kitchenware & Appliances', 'slug': 'kitchenware-appliances'},
                    {'name': 'Bedding & Bath', 'slug': 'bedding-bath'},
                    {'name': 'Lighting & Fixtures', 'slug': 'lighting-fixtures'},
                ]
            },
            {
                'name': 'Beauty & Personal Care',
                'slug': 'beauty-personal-care',
                'subcategories': [
                    {'name': 'Skincare', 'slug': 'skincare'},
                    {'name': 'Haircare', 'slug': 'haircare'},
                    {'name': 'Makeup & Cosmetics', 'slug': 'makeup-cosmetics'},
                    {'name': 'Fragrances & Perfumes', 'slug': 'fragrances-perfumes'},
                    {'name': 'Personal Hygiene', 'slug': 'personal-hygiene'},
                ]
            },
            {
                'name': 'Sports, Fitness & Outdoors',
                'slug': 'sports-fitness-outdoors',
                'subcategories': [
                    {'name': 'Exercise & Fitness Equipment', 'slug': 'exercise-fitness-equipment'},
                    {'name': 'Outdoor Recreation & Camping', 'slug': 'outdoor-recreation-camping'},
                    {'name': 'Athletic Apparel', 'slug': 'athletic-apparel'},
                    {'name': 'Cycling & Scooters', 'slug': 'cycling-scooters'},
                ]
            },
            {
                'name': 'Toys, Games & Hobbies',
                'slug': 'toys-games-hobbies',
                'subcategories': [
                    {'name': 'Action Figures & Toys', 'slug': 'action-figures-toys'},
                    {'name': 'Board Games & Puzzles', 'slug': 'board-games-puzzles'},
                    {'name': 'Crafts & Hobbies', 'slug': 'crafts-hobbies'},
                ]
            },
            {
                'name': 'Automotive & Hardware',
                'slug': 'automotive-hardware',
                'subcategories': [
                    {'name': 'Car Accessories', 'slug': 'car-accessories'},
                    {'name': 'Auto Parts', 'slug': 'auto-parts'},
                    {'name': 'Hand & Power Tools', 'slug': 'hand-power-tools'},
                ]
            },
            {
                'name': 'Books, Media & Stationery',
                'slug': 'books-media-stationery',
                'subcategories': [
                    {'name': 'Books & Literature', 'slug': 'books-literature'},
                    {'name': 'Office & School Supplies', 'slug': 'office-school-supplies'},
                    {'name': 'Music & Video', 'slug': 'music-video'},
                ]
            },
            {
                'name': 'Grocery & Gourmet Food',
                'slug': 'grocery-gourmet-food',
                'subcategories': [
                    {'name': 'Beverages & Coffee', 'slug': 'beverages-coffee'},
                    {'name': 'Snacks & Confectionery', 'slug': 'snacks-confectionery'},
                    {'name': 'Pantry Staples', 'slug': 'pantry-staples'},
                ]
            },
            {
                'name': 'Digital Goods & Services',
                'slug': 'digital-goods-services',
                'subcategories': [
                    {'name': 'Software & Licenses', 'slug': 'software-licenses'},
                    {'name': 'E-books & Digital Courses', 'slug': 'ebooks-digital-courses'},
                ]
            }
        ]

        categories_created = 0
        subcategories_created = 0

        for cat_data in global_categories_data:
            parent_cat, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults={
                    'name': cat_data['name'],
                    'tenant_id': None  # None = Global / Shared across all shops
                }
            )
            if created:
                categories_created += 1

            for sub_data in cat_data.get('subcategories', []):
                _, sub_created = Category.objects.get_or_create(
                    slug=sub_data['slug'],
                    defaults={
                        'name': sub_data['name'],
                        'parent': parent_cat,
                        'tenant_id': None
                    }
                )
                if sub_created:
                    subcategories_created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Created {categories_created} main global categories and {subcategories_created} global subcategories."
        ))

        # --- 2. GLOBAL COMMON PRODUCT ATTRIBUTES & VALUES ---
        global_attributes_data = [
            {
                'name': 'Color',
                'category': 'COLOR',
                'display_order': 1,
                'values': [
                    {'value': 'Black', 'code': '#000000'},
                    {'value': 'White', 'code': '#FFFFFF'},
                    {'value': 'Red', 'code': '#FF0000'},
                    {'value': 'Blue', 'code': '#0000FF'},
                    {'value': 'Green', 'code': '#008000'},
                    {'value': 'Yellow', 'code': '#FFFF00'},
                    {'value': 'Gold', 'code': '#FFD700'},
                    {'value': 'Silver', 'code': '#C0C0C0'},
                    {'value': 'Grey', 'code': '#808080'},
                    {'value': 'Purple', 'code': '#800080'},
                    {'value': 'Pink', 'code': '#FFC0CB'},
                    {'value': 'Brown', 'code': '#A52A2A'},
                ]
            },
            {
                'name': 'Size',
                'category': 'SIZE',
                'display_order': 2,
                'values': [
                    {'value': 'XS', 'code': 'XS'},
                    {'value': 'S', 'code': 'S'},
                    {'value': 'M', 'code': 'M'},
                    {'value': 'L', 'code': 'L'},
                    {'value': 'XL', 'code': 'XL'},
                    {'value': 'XXL', 'code': 'XXL'},
                    {'value': '3XL', 'code': '3XL'},
                    {'value': '28', 'code': '28'},
                    {'value': '30', 'code': '30'},
                    {'value': '32', 'code': '32'},
                    {'value': '34', 'code': '34'},
                    {'value': '36', 'code': '36'},
                    {'value': '38', 'code': '38'},
                    {'value': '40', 'code': '40'},
                ]
            },
            {
                'name': 'Gender / Target Audience',
                'category': 'SPECIFICATION',
                'display_order': 3,
                'values': [
                    {'value': 'Men', 'code': 'MEN'},
                    {'value': 'Women', 'code': 'WOMEN'},
                    {'value': 'Unisex', 'code': 'UNISEX'},
                    {'value': 'Kids', 'code': 'KIDS'},
                    {'value': 'Babies', 'code': 'BABIES'},
                ]
            },
            {
                'name': 'Condition',
                'category': 'SPECIFICATION',
                'display_order': 4,
                'values': [
                    {'value': 'Brand New', 'code': 'NEW'},
                    {'value': 'Refurbished', 'code': 'REFURBISHED'},
                    {'value': 'Used - Like New', 'code': 'LIKE_NEW'},
                    {'value': 'Used - Good', 'code': 'GOOD'},
                ]
            },
            {
                'name': 'Material',
                'category': 'MATERIAL',
                'display_order': 5,
                'values': [
                    {'value': 'Cotton', 'code': 'COTTON'},
                    {'value': 'Leather', 'code': 'LEATHER'},
                    {'value': 'Polyester', 'code': 'POLYESTER'},
                    {'value': 'Stainless Steel', 'code': 'STEEL'},
                    {'value': 'Wood', 'code': 'WOOD'},
                    {'value': 'Plastic', 'code': 'PLASTIC'},
                    {'value': 'Denim', 'code': 'DENIM'},
                    {'value': 'Silk', 'code': 'SILK'},
                    {'value': 'Glass', 'code': 'GLASS'},
                ]
            }
        ]

        attributes_created = 0
        values_created = 0

        for attr_data in global_attributes_data:
            attr_obj, created = ProductAttribute.objects.get_or_create(
                name=attr_data['name'],
                tenant_id=None,
                defaults={
                    'category': attr_data['category'],
                    'display_order': attr_data['display_order']
                }
            )
            if created:
                attributes_created += 1

            for val_data in attr_data.get('values', []):
                _, val_created = ProductAttributeValue.objects.get_or_create(
                    attribute=attr_obj,
                    value=val_data['value'],
                    defaults={
                        'code': val_data.get('code', '')
                    }
                )
                if val_created:
                    values_created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Created {attributes_created} global attributes and {values_created} global attribute values."
        ))

        self.stdout.write(self.style.SUCCESS("Successfully completed Global Catalog Seeding!"))
