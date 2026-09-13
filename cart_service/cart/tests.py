import uuid
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from cart.models import Cart, CartItem, Wishlist, WishlistItem, ItemRequest


class CartViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        from django.contrib.auth.models import User
        self.user = User.objects.create_user(username='cartuser', password='pass123')
        self.client.force_authenticate(user=self.user)

    def test_create_cart(self):
        response = self.client.post('/api/cart/carts/', {})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Cart.objects.filter(user_id=self.user.id).count(), 1)

    def test_list_carts_returns_only_own(self):
        Cart.objects.create(user_id=self.user.id)
        Cart.objects.create(user_id=uuid.uuid4())
        response = self.client.get('/api/cart/carts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 1)

    def test_add_item_to_cart(self):
        cart = Cart.objects.create(user_id=self.user.id)
        url = '/api/cart/carts/add-item/'
        data = {'product_id': str(uuid.uuid4()), 'quantity': 2, 'price': '19.99'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CartItem.objects.filter(cart=cart).count(), 1)

    def test_add_item_invalid_data_fails(self):
        cart = Cart.objects.create(user_id=self.user.id)
        url = '/api/cart/carts/add-item/'
        response = self.client.post(url, {'product_id': 'bad-uuid', 'quantity': 1, 'price': '10.00'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_remove_item_from_cart(self):
        cart = Cart.objects.create(user_id=self.user.id)
        item = CartItem.objects.create(cart=cart, product_id=uuid.uuid4(), quantity=1, price='5.00')
        url = '/api/cart/carts/remove-item/'
        response = self.client.post(url, {'item_id': str(item.id)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(CartItem.objects.filter(id=item.id).exists())

    def test_unauthenticated_cart_access_fails(self):
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/cart/carts/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_cart(self):
        cart = Cart.objects.create(user_id=self.user.id)
        response = self.client.delete(f'/api/cart/carts/{cart.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Cart.objects.filter(id=cart.id).exists())

    def test_apply_coupon_to_cart(self):
        cart = Cart.objects.create(user_id=self.user.id)
        CartItem.objects.create(cart=cart, product_id=uuid.uuid4(), quantity=2, price='50.00')
        url = '/api/cart/carts/apply-coupon/'
        response = self.client.post(url, {'coupon_code': 'SAVE10'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['coupon_code'], 'SAVE10')
        self.assertEqual(float(response.data['discount_amount']), 10.00)
        self.assertEqual(float(response.data['total']), 90.00)


class WishlistViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        from django.contrib.auth.models import User
        self.user = User.objects.create_user(username='wishuser', password='pass123')
        self.client.force_authenticate(user=self.user)

    def test_create_wishlist(self):
        response = self.client.post('/api/cart/wishlists/', {'name': 'Favorites'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Wishlist.objects.filter(user_id=self.user.id).count(), 1)

    def test_list_wishlists_returns_only_own(self):
        Wishlist.objects.create(user_id=self.user.id, name='Mine')
        Wishlist.objects.create(user_id=uuid.uuid4(), name='Others')
        response = self.client.get('/api/cart/wishlists/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 1)

    def test_add_item_to_wishlist(self):
        wishlist = Wishlist.objects.create(user_id=self.user.id, name='WL')
        url = '/api/cart/wishlists/add-item/'
        data = {'product_id': str(uuid.uuid4()), 'note': 'Want this'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(WishlistItem.objects.filter(wishlist=wishlist).count(), 1)

    def test_remove_item_from_wishlist(self):
        wishlist = Wishlist.objects.create(user_id=self.user.id, name='WL2')
        item = WishlistItem.objects.create(wishlist=wishlist, product_id=uuid.uuid4())
        url = '/api/cart/wishlists/remove-item/'
        response = self.client.post(url, {'item_id': str(item.id)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(WishlistItem.objects.filter(id=item.id).exists())

    def test_unauthenticated_wishlist_access_fails(self):
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/cart/wishlists/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ItemRequestViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        from django.contrib.auth.models import User
        self.user = User.objects.create_user(username='requser', password='pass123')
        self.client.force_authenticate(user=self.user)

    def test_create_item_request(self):
        data = {'product_name': 'Special Widget', 'description': 'Need it urgently', 'quantity': 3}
        response = self.client.post('/api/cart/item-requests/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ItemRequest.objects.filter(user_id=self.user.id).count(), 1)

    def test_create_item_request_default_status_pending(self):
        self.client.post('/api/cart/item-requests/', {'product_name': 'Widget', 'quantity': 1})
        req = ItemRequest.objects.first()
        self.assertEqual(req.status, 'PENDING')

    def test_list_item_requests_returns_only_own(self):
        ItemRequest.objects.create(user_id=self.user.id, product_name='Mine', quantity=1)
        ItemRequest.objects.create(user_id=uuid.uuid4(), product_name='Others', quantity=1)
        response = self.client.get('/api/cart/item-requests/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 1)

    def test_create_item_request_missing_product_name_fails(self):
        response = self.client.post('/api/cart/item-requests/', {'quantity': 1})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_item_request_fails(self):
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/cart/item-requests/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

