from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from .models import WishlistCollection, WishlistItem
from product.models import MenuItem
import json
import sys
import logging
logging.basicConfig(
    level=logging.INFO,  # atau logging.DEBUG untuk lebih detail
    format='%(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

class WishlistCollectionModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            password='testpass123'
        )

    def test_collection_creation(self):
        collection = WishlistCollection.objects.create(
            name="Test Collection",
            user=self.user,
            description="Test Description"
        )
        self.assertEqual(str(collection), "Test Collection - testuser's Collection")
        self.assertFalse(collection.is_default)

    def test_default_collection_uniqueness(self):
        # Create first default collection
        collection1 = WishlistCollection.objects.create(
            name="Collection 1",
            user=self.user,
            is_default=True
        )
        # Create second default collection
        collection2 = WishlistCollection.objects.create(
            name="Collection 2",
            user=self.user,
            is_default=True
        )
        
        # Refresh from database
        collection1.refresh_from_db()
        collection2.refresh_from_db()
        
        # Check that only collection2 is now default
        self.assertFalse(collection1.is_default)
        self.assertTrue(collection2.is_default)

    def test_collection_name_uniqueness_per_user(self):
        WishlistCollection.objects.create(
            name="Test Collection",
            user=self.user
        )
        # Same name for different user should work
        collection2 = WishlistCollection.objects.create(
            name="Test Collection",
            user=self.user2
        )
        self.assertTrue(collection2.id is not None)
        
        # Same name for same user should fail
        with self.assertRaises(Exception):
            WishlistCollection.objects.create(
                name="Test Collection",
                user=self.user
            )

class WishlistItemModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.collection = WishlistCollection.objects.create(
            name="Test Collection",
            user=self.user
        )
        self.menu_item = MenuItem.objects.create(
            name="Test Item",
            price=10.00
        )

    def test_wishlist_item_creation(self):
        item = WishlistItem.objects.create(
            collection=self.collection,
            menu_item=self.menu_item
        )
        print(str)
        self.assertEqual(str(item), "Test Item in Test Collection")
        self.assertTrue(isinstance(item.created_at, timezone.datetime))

    def test_wishlist_item_uniqueness_per_collection(self):
        WishlistItem.objects.create(
            collection=self.collection,
            menu_item=self.menu_item
        )
        # Same item in same collection should fail
        with self.assertRaises(Exception):
            WishlistItem.objects.create(
                collection=self.collection,
                menu_item=self.menu_item
            )

class WishlistViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.collection = WishlistCollection.objects.create(
            name="Test Collection",
            user=self.user
        )
        self.menu_item = MenuItem.objects.create(
            name="Test Item",
            price=10.00
        )
        self.client.login(username='testuser', password='testpass123')

    def test_collection_list_view(self):
        response = self.client.get(reverse('wishlist:collection-list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'collections.html')

    def test_collection_add_view(self):
        # Login user dulu
        self.client.login(username='testuser', password='testpass123')
        
        # Test tambah collection
        response = self.client.post(reverse('wishlist:collection-add'), {
            'name': 'New Collection',
            'description': 'New Description'
        })
        
        # Cek redirect dan collection berhasil dibuat
        # self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertTrue(
            WishlistCollection.objects.filter(
                name='New Collection',
                user=self.user  # Pastikan collection terbuat untuk user yang benar
            ).exists()
        )
        
        # Optional: Tambahan pengecekan
        collection = WishlistCollection.objects.get(name='New Collection')
        self.assertEqual(collection.description, 'New Description')
        self.assertEqual(collection.user, self.user)

    def test_collection_detail_view(self):
        response = self.client.get(
            reverse('wishlist:collection-detail', 
                   kwargs={'collection_id': self.collection.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'collection_detail.html')

    def test_collection_edit_view(self):
        response = self.client.post(
            reverse('wishlist:collection-edit', 
                   kwargs={'collection_id': self.collection.id}),
            {
                'name': 'Updated Collection',
                'description': 'Updated Description'
            }
        )
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.collection.refresh_from_db()
        self.assertEqual(self.collection.name, 'Updated Collection')

    def test_collection_delete_view(self):
        response = self.client.post(
            reverse('wishlist:collection-delete', 
                   kwargs={'collection_id': self.collection.id})
        )
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertFalse(
            WishlistCollection.objects.filter(id=self.collection.id).exists()
        )

    def test_item_add_view(self):
        response = self.client.post(
            reverse('wishlist:item-add', 
                   kwargs={'menu_item_id': self.menu_item.id}),
            data=json.dumps({'collection_id': self.collection.id}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            WishlistItem.objects.filter(
                collection=self.collection,
                menu_item=self.menu_item
            ).exists()
        )

    def test_unauthenticated_access(self):
        self.client.logout()
        response = self.client.get(reverse('wishlist:collection-list'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_create_collection_ajax(self):
        response = self.client.post(
            reverse('wishlist:create-collection-ajax'),
            {
                'name': 'Ajax Collection',
                'description': 'Created via AJAX'
            }
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)
        self.assertTrue('collection_id' in data)
        self.assertTrue(
            WishlistCollection.objects.filter(name='Ajax Collection').exists()
        )

    def test_default_collection_behavior(self):
        # Test that default collection is created if it doesn't exist
        response = self.client.get(reverse('wishlist:collection-list'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            WishlistCollection.objects.filter(
                user=self.user,
                name="My Wishlist",
                is_default=True
            ).exists()
        )

    def test_item_move_view(self):
        # Create two collections and an item
        collection2 = WishlistCollection.objects.create(
            name="Second Collection",
            user=self.user
        )
        item = WishlistItem.objects.create(
            collection=self.collection,
            menu_item=self.menu_item
        )
        
        response = self.client.post(
            reverse('wishlist:item-move', kwargs={
                'item_id': item.id,
                'collection_id': collection2.id
            })
        )
        self.assertEqual(response.status_code, 200)
        item.refresh_from_db()
        self.assertEqual(item.collection, collection2)