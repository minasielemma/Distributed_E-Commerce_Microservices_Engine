import uuid
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework import status

from catalog.models import (
    Category, Product, ProductPrice, ProductLike, PriceDiscount,
    ProductAttribute, ProductAttributeValue, ProductVariant,
    ProductImage, ProductReview, DiscountCode
)


class CategoryViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_list_categories_public(self):
        Category.objects.create(name='Electronics', slug='electronics', is_global=True)
        response = self.client.get('/api/catalog/storefront/categories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results'] if isinstance(response.data, dict) and 'results' in response.data else response.data
        self.assertEqual(len(results), 1)

    def test_list_only_root_categories(self):
        parent = Category.objects.create(name='Parent', slug='parent', is_global=True)
        Category.objects.create(name='Child', slug='child', parent=parent, is_global=True)
        response = self.client.get('/api/catalog/storefront/categories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results'] if isinstance(response.data, dict) and 'results' in response.data else response.data
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'Parent')

    def test_category_includes_subcategories(self):
        parent = Category.objects.create(name='Parent', slug='parent', is_global=True)
        Category.objects.create(name='Sub', slug='sub', parent=parent, is_global=True)
        response = self.client.get('/api/catalog/storefront/categories/')
        results = response.data['results'] if isinstance(response.data, dict) and 'results' in response.data else response.data
        self.assertEqual(len(results), 1)
        self.assertEqual(len(results[0]['subcategories']), 1)

    def test_create_category_authenticated(self):
        from django.contrib.auth.models import User
        user = User.objects.create_user(username='catuser', password='pass123')
        user.role = 'STORE_OWNER'
        user.tenant_id = uuid.uuid4()
        user.save()
        self.client.force_authenticate(user=user)
        response = self.client.post('/api/catalog/categories/', {'name': 'Books', 'slug': 'books'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_delete_subcategory(self):
        from django.contrib.auth.models import User
        tid = uuid.uuid4()
        user = User.objects.create_user(username='deluser', password='pass123')
        user.role = 'STORE_OWNER'
        user.tenant_id = tid
        user.save()
        self.client.force_authenticate(user=user)
        parent = Category.objects.create(name='Parent', slug='parent', tenant_id=tid)
        sub = Category.objects.create(name='Sub', slug='sub', parent=parent, tenant_id=tid)
        response = self.client.delete(f'/api/catalog/categories/{sub.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Category.objects.filter(id=sub.id).exists())

    def test_search_categories(self):
        Category.objects.create(name='Electronics', slug='electronics', is_global=True)
        Category.objects.create(name='Clothing', slug='clothing', is_global=True)
        response = self.client.get('/api/catalog/storefront/categories/', {'search': 'Elec'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results'] if isinstance(response.data, dict) and 'results' in response.data else response.data
        self.assertEqual(len(results), 1)


class ProductViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        from django.contrib.auth.models import User
        self.user = User.objects.create_user(username='produser', password='pass123')
        self.user.role = 'STORE_OWNER'
        self.user.tenant_id = uuid.uuid4()
        self.user.save()
        self.category = Category.objects.create(name='Tech', slug='tech')

    def test_list_products_public(self):
        Product.objects.create(name='Laptop', sku='LAP001', category=self.category)
        response = self.client.get('/api/catalog/storefront/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results'] if isinstance(response.data, dict) and 'results' in response.data else response.data
        self.assertEqual(len(results), 1)

    def test_unauthenticated_can_list_and_retrieve_products(self):
        prod = Product.objects.create(name='Public Product', sku='PUB001', category=self.category)
        # List products without auth
        res_list = self.client.get('/api/catalog/products/')
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)
        # Retrieve single product without auth
        res_detail = self.client.get(f'/api/catalog/products/{prod.id}/')
        self.assertEqual(res_detail.status_code, status.HTTP_200_OK)
        self.assertEqual(res_detail.data['name'], 'Public Product')

    def test_unauthenticated_cannot_create_product(self):
        response = self.client.post('/api/catalog/products/', {'name': 'Unauthorized Product', 'sku': 'UNAUTH001'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_product_with_price(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'name': 'Phone', 'sku': 'PHN001',
            'category': str(self.category.id),
            'price_detail': {'base_price': '299.99', 'cost_price': '150.00', 'currency': 'USD'}
        }
        response = self.client.post('/api/catalog/products/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(ProductPrice.objects.filter(product__sku='PHN001').exists())

    def test_create_product_without_price_creates_default_price(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/catalog/products/', {'name': 'Tablet', 'sku': 'TAB001'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(ProductPrice.objects.filter(product__sku='TAB001').exists())

    def test_filter_products_by_category(self):
        other_cat = Category.objects.create(name='Other', slug='other')
        Product.objects.create(name='P1', sku='P001', category=self.category)
        Product.objects.create(name='P2', sku='P002', category=other_cat)
        response = self.client.get('/api/catalog/storefront/products/', {'category_id': str(self.category.id)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results'] if isinstance(response.data, dict) and 'results' in response.data else response.data
        self.assertEqual(len(results), 1)

    def test_filter_products_by_tenant_id(self):
        t1 = uuid.uuid4()
        t2 = uuid.uuid4()
        Product.objects.create(name='Shop 1 Product', sku='S1P1', tenant_id=t1)
        Product.objects.create(name='Shop 2 Product', sku='S2P1', tenant_id=t2)
        
        # Test query param tenant_id
        res1 = self.client.get('/api/catalog/storefront/products/', {'tenant_id': str(t1)})
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        results1 = res1.data['results'] if isinstance(res1.data, dict) and 'results' in res1.data else res1.data
        self.assertEqual(len(results1), 1)
        self.assertEqual(results1[0]['sku'], 'S1P1')

        # Test query param shop
        res2 = self.client.get('/api/catalog/storefront/products/', {'shop': str(t2)})
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        results2 = res2.data['results'] if isinstance(res2.data, dict) and 'results' in res2.data else res2.data
        self.assertEqual(len(results2), 1)
        self.assertEqual(results2[0]['sku'], 'S2P1')

        # Test HTTP header X-Tenant-ID
        res3 = self.client.get('/api/catalog/storefront/products/', HTTP_X_TENANT_ID=str(t1))
        self.assertEqual(res3.status_code, status.HTTP_200_OK)
        results3 = res3.data['results'] if isinstance(res3.data, dict) and 'results' in res3.data else res3.data
        self.assertEqual(len(results3), 1)
        self.assertEqual(results3[0]['sku'], 'S1P1')

    def test_like_product_authenticated(self):
        self.client.force_authenticate(user=self.user)
        product = Product.objects.create(name='Camera', sku='CAM001', tenant_id=self.user.tenant_id)
        url = f'/api/catalog/products/{product.id}/like/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'liked')
        self.assertEqual(ProductLike.objects.filter(product=product).count(), 1)

    def test_unlike_product_on_second_like(self):
        self.client.force_authenticate(user=self.user)
        product = Product.objects.create(name='Camera2', sku='CAM002', tenant_id=self.user.tenant_id)
        ProductLike.objects.create(user_id=self.user.id, product=product)
        url = f'/api/catalog/products/{product.id}/like/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'unliked')
        self.assertEqual(ProductLike.objects.filter(product=product).count(), 0)

    def test_like_product_unauthenticated_fails(self):
        product = Product.objects.create(name='Watch', sku='WTC001')
        url = f'/api/catalog/products/{product.id}/like/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class VariantAndAttributeTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        from django.contrib.auth.models import User
        self.user = User.objects.create_user(username='varuser', password='pass123')
        self.user.role = 'STORE_OWNER'
        self.user.tenant_id = uuid.uuid4()
        self.user.save()
        self.client.force_authenticate(user=self.user)
        self.product = Product.objects.create(name='Shirt', sku='SHIRT01', tenant_id=self.user.tenant_id)
        self.color_attr = ProductAttribute.objects.create(name='Color', category='COLOR', tenant_id=self.user.tenant_id)
        self.val_red = ProductAttributeValue.objects.create(attribute=self.color_attr, value='Red', code='#FF0000')

    def test_create_variant_with_attribute(self):
        variant = ProductVariant.objects.create(product=self.product, sku='SHIRT-RED-L', price=Decimal('25.00'), stock=10)
        variant.attribute_values.add(self.val_red)
        response = self.client.get(f'/api/catalog/variants/{variant.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['sku'], 'SHIRT-RED-L')
        self.assertEqual(len(response.data['attribute_values_detail']), 1)


class ProductReviewAndCouponTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.product = Product.objects.create(name='Shoe', sku='SHOE01')
        from django.contrib.auth.models import User
        self.user = User.objects.create_user(username='reviewer', password='pass123')

    def test_create_review(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'product': str(self.product.id),
            'rating': 5,
            'title': 'Great shoes',
            'review_text': 'Fits perfectly!'
        }
        response = self.client.post('/api/catalog/reviews/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ProductReview.objects.filter(product=self.product).count(), 1)

    def test_create_anonymous_review(self):
        # Do not authenticate user
        data = {
            'product': str(self.product.id),
            'rating': 4,
            'title': 'Nice product',
            'review_text': 'Bought without login'
        }
        response = self.client.post('/api/catalog/reviews/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        review = ProductReview.objects.get(product=self.product, title='Nice product')
        self.assertIsNone(review.user_id)
        self.assertEqual(review.user_name, 'Anonymous')

    def test_validate_discount_code(self):
        coupon = DiscountCode.objects.create(
            code='SAVE20',
            discount_type='PERCENTAGE',
            value=Decimal('20.00'),
            min_purchase_amount=Decimal('50.00'),
            is_active=True
        )
        response = self.client.post('/api/catalog/coupons/validate/', {'code': 'SAVE20', 'subtotal': '100.00'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['valid'])
        self.assertEqual(response.data['discount_amount'], '20.00')

    def test_create_discount_code(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'code': 'FALL50',
            'discount_type': 'FIXED',
            'value': '50.00',
            'min_purchase_amount': '150.00',
            'usage_limit': 50,
            'is_active': True
        }
        response = self.client.post('/api/catalog/coupons/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DiscountCode.objects.filter(code='FALL50').count(), 1)

    def test_create_discount_code_with_aliases(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'code': 'SUMMER10',
            'discount_type': 'PERCENTAGE',
            'discount_value': '10.00',
            'min_order_amount': '30.00',
            'max_uses': 200,
            'is_active': True
        }
        response = self.client.post('/api/catalog/coupons/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        code_obj = DiscountCode.objects.get(code='SUMMER10')
        self.assertEqual(code_obj.value, Decimal('10.00'))
        self.assertEqual(code_obj.min_purchase_amount, Decimal('30.00'))
        self.assertEqual(code_obj.usage_limit, 200)

