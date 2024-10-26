# dashboard/tests.py
from django.http import HttpResponseRedirect
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from authentication.models import UserProfile
from product.models import MenuItem
from restaurant.models import Restaurant
from review.models import ReviewEntry
from decimal import Decimal
import json

class DashboardViewsTest(TestCase):
    def setUp(self):
        # Set up test client
        self.client = Client()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create user profile
        self.profile = UserProfile.objects.create(
            user=self.user,
            user_type='USER',
            username='testuser',
            fullname='Test User',
            country='Indonesia'
        )
        
        # Create test admin
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            is_staff=True
        )
        
        self.admin_profile = UserProfile.objects.create(
            user=self.admin_user,
            user_type='ADMIN',
            username='admin',
            fullname='Administrator',
            country='Indonesia'
        )
        
        # Create test restaurant
        self.restaurant = Restaurant.objects.create(
            name='Test Restaurant',
            city='Jakarta',
            kecamatan='Kebayoran Baru',
            location='Test Location'
        )
        
        # Create test menu items
        self.menu_item = MenuItem.objects.create(
            name='Test Food',
            image='http://example.com/food.jpg',
            description='Test description',
            category='Makanan Tradisional',
            price=Decimal('50000.00'),
            restaurant=self.restaurant
        )
        
        # Create another menu item for search testing
        self.menu_item2 = MenuItem.objects.create(
            name='Special Nasi Goreng',
            image='http://example.com/food2.jpg',
            description='Another test description',
            category='Makanan Tradisional',
            price=Decimal('45000.00'),
            restaurant=self.restaurant
        )
        
        # Create test review
        self.review = ReviewEntry.objects.create(
            user=self.user,
            menu_item=self.menu_item,
            rating=4.5,
            review_text='Great food!'
        )

    def test_initialize_admin(self):
        response = self.client.get(reverse('dashboard:initialize_admin'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Admin berhasil diinisialisasi.")
        
        # Check if admin user was created correctly
        admin = User.objects.get(username='admin')
        self.assertTrue(admin.is_staff)
        self.assertEqual(admin.userprofile.user_type, 'ADMIN')

    def test_is_admin(self):
        from dashboard.views import is_admin
        
        # Test admin user
        self.assertTrue(is_admin(self.admin_user))
        
        # Test regular user
        self.assertFalse(is_admin(self.user))
        
        # Test unauthenticated user
        class AnonymousUser:
            @property
            def is_authenticated(self):
                return False
        
        anonymous_user = AnonymousUser()
        self.assertFalse(is_admin(anonymous_user))

    def test_makanan_list(self):
        response = self.client.get(reverse('dashboard:makanan_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'makanan_list.html')
        
        # Test with filters
        response = self.client.get(
            reverse('dashboard:makanan_list'),
            {'category': 'Makanan Tradisional', 'kecamatan': 'Kebayoran Baru'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('makanans', response.context)

        # Test min price filter
        response = self.client.get(
            reverse('dashboard:makanan_list'),
            {'min_price': '40000'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(makanan['price'] >= 40000 for makanan in response.context['makanans']))

        # Test max price filter
        response = self.client.get(
            reverse('dashboard:makanan_list'),
            {'max_price': '60000'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(all(makanan['price'] <= 60000 for makanan in response.context['makanans']))

        # Test both min and max price filters
        response = self.client.get(
            reverse('dashboard:makanan_list'),
            {'min_price': '40000', 'max_price': '60000'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            all(40000 <= makanan['price'] <= 60000 
                for makanan in response.context['makanans'])
        )
        # Test search filter
        # Test exact match
        response = self.client.get(
            reverse('dashboard:makanan_list'),
            {'search': 'Test Food'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('makanans', response.context)
        makanans = response.context['makanans']
        self.assertTrue(any(m['item'] == 'Test Food' for m in makanans))
        self.assertFalse(any(m['item'] == 'Special Nasi Goreng' for m in makanans))

        # Test partial match
        response = self.client.get(
            reverse('dashboard:makanan_list'),
            {'search': 'Nasi'}
        )
        self.assertEqual(response.status_code, 200)
        makanans = response.context['makanans']
        self.assertTrue(any(m['item'] == 'Special Nasi Goreng' for m in makanans))
        self.assertFalse(any(m['item'] == 'Test Food' for m in makanans))

        # Test case-insensitive match
        response = self.client.get(
            reverse('dashboard:makanan_list'),
            {'search': 'test'}
        )
        self.assertEqual(response.status_code, 200)
        makanans = response.context['makanans']
        self.assertTrue(any(m['item'] == 'Test Food' for m in makanans))

        # Test no match
        response = self.client.get(
            reverse('dashboard:makanan_list'),
            {'search': 'NonexistentFood'}
        )
        self.assertEqual(response.status_code, 200)
        makanans = response.context['makanans']
        self.assertEqual(len(makanans), 0)

    def test_restaurant_menu(self):
        response = self.client.get(
            reverse('dashboard:restaurant_menu', 
                   kwargs={'resto_name': self.restaurant.name})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'resto_menu.html')
        
        # Test non-existent restaurant
        response = self.client.get(
            reverse('dashboard:restaurant_menu', 
                   kwargs={'resto_name': 'NonExistentRestaurant'})
        )
        self.assertEqual(response.status_code, 404)

    def test_restaurant_list(self):
        response = self.client.get(reverse('dashboard:restaurant_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'resto_list.html')
        
        # Test with filters
        response = self.client.get(
            reverse('dashboard:restaurant_list'),
            {'kecamatan': 'Kebayoran Baru', 'search': 'Test'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('restaurants', response.context)

    def test_restaurant_update_form(self):
        """Test restaurant update functionality"""
        self.client.login(username='admin', password='admin123')
        
        # Test GET request
        response = self.client.get(
            reverse('dashboard:restaurant_update', 
                    kwargs={'resto_name': self.restaurant.name})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'update_restaurant.html')
        
        # Test POST with valid data
        update_data = {
            'name': 'Updated Restaurant',
            'city': 'Jakarta',
            'kecamatan': 'Kebayoran Baru',
            'location': 'Updated Location'
        }
        response = self.client.post(
            reverse('dashboard:restaurant_update', 
                    kwargs={'resto_name': self.restaurant.name}),
            update_data
        )
        self.assertRedirects(
            response, 
            reverse('dashboard:restaurant_menu', 
                    kwargs={'resto_name': 'Updated Restaurant'})
        )
        
        # Test POST with invalid data
        invalid_data = {
            'name': '',  # Invalid: empty name
            'city': 'Jakarta',
            'kecamatan': 'Invalid Kecamatan',  # Invalid choice
            'location': 'Test'
        }
        response = self.client.post(
            reverse('dashboard:restaurant_update', 
                    kwargs={'resto_name': 'Updated Restaurant'}),
            invalid_data
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'update_restaurant.html')

    def test_makanan_create(self):
        self.client.login(username='admin', password='admin123')
        
        post_data = {
            'name': 'New Food',
            'description': 'New description',
            'price': '75000.00',
            'image': 'http://example.com/newfood.jpg',
            'category': 'Makanan Tradisional',
            'resto_name': self.restaurant.name,
            'kecamatan': 'Kebayoran Baru',
            'location': 'New Location'
        }
        
        response = self.client.post(
            reverse('dashboard:makanan_create'),
            post_data
        )
        self.assertEqual(response.status_code, 201)
        
        # Verify the menu item was created
        self.assertTrue(
            MenuItem.objects.filter(name='New Food').exists()
        )

    def test_makanan_create_invalid(self):
        """Test makanan create with invalid data"""
        self.client.login(username='admin', password='admin123')
        
        # Test with invalid data
        invalid_data = {
            'name': '',  # Invalid: empty name
            'description': 'Test description',
            'price': 'invalid_price',  # Invalid: not a number
            'image': 'not_a_url',  # Invalid: not a URL
            'category': 'Invalid Category',  # Invalid choice
            'resto_name': 'NonExistent Restaurant'
        }
        
        response = self.client.post(
            reverse('dashboard:makanan_create'),
            invalid_data
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, b"ERROR")

    def test_makanan_update(self):
        self.client.login(username='admin', password='admin123')
        
        # Test GET request - should show form
        response = self.client.get(
            reverse('dashboard:makanan_update', kwargs={'id': self.menu_item.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'update_makanan.html')
        
        # Test POST request with valid data
        update_data = {
            'name': 'Updated Food',
            'description': 'Updated description',
            'price': '60000.00',
            'image': 'http://example.com/updated.jpg',
            'category': 'Makanan Tradisional',
            'restaurant': self.restaurant.id,
            'resto_name': self.restaurant.name,
            'kecamatan': self.restaurant.kecamatan,
            'location': self.restaurant.location
            
        }
        
        response = self.client.post(
            reverse('dashboard:makanan_update', kwargs={'id': self.menu_item.id}),
            update_data
        )
        
        expected_url = reverse('dashboard:makanan_list') 
        # Assert the response status directly 
        self.assertEqual(response.status_code, 302)
        # Confirm the redirect URL is as expected 
        self.assertRedirects(response, expected_url) 
        
        # Verify the menu item was updated regardless of response type
        updated_item = MenuItem.objects.get(id=self.menu_item.id)
        if response.status_code == 302:  # Only check if update was successful
            self.assertEqual(updated_item.name, 'Updated Food')
            self.assertEqual(updated_item.description, 'Updated description')
        
        # Test POST request with invalid data
        invalid_data = {
            'name': '',  # Invalid: empty name
            'description': 'Updated description',
            'price': '60000.00',
            'image': 'http://example.com/updated.jpg',
            'category': 'Makanan Tradisional',
            'restaurant': self.restaurant.id
        }
        
        response = self.client.post(
            reverse('dashboard:makanan_update', kwargs={'id': self.menu_item.id}),
            invalid_data
        )
        self.assertEqual(response.status_code, 200)  # Should re-render form with errors
        self.assertTemplateUsed(response, 'update_makanan.html')

    def test_makanan_update_resto(self):
        """Test updating menu item from restaurant view"""
        self.client.login(username='admin', password='admin123')
        
        # Test GET request
        response = self.client.get(
            reverse('dashboard:makanan_update_resto', kwargs={'id': self.menu_item.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'update_makanan_resto.html')
        
        # Test POST with valid data
        update_data = {
            'name': 'Updated Food Item',
            'description': 'Updated description',
            'price': '75000.00',
            'image': 'http://example.com/food.jpg',
            'category': 'Makanan Tradisional',
            'restaurant': self.restaurant.id,
            'resto_name': self.restaurant.name,
            'kecamatan': self.restaurant.kecamatan,
            'location': self.restaurant.location
        }
        response = self.client.post(
            reverse('dashboard:makanan_update_resto', kwargs={'id': self.menu_item.id}),
            update_data
        )

        expected_url = reverse('dashboard:restaurant_menu', kwargs={'resto_name': self.restaurant.name})
                
        # Assert the response status directly
        self.assertEqual(response.status_code, 302)

        # Confirm the redirect URL is as expected
        self.assertRedirects(response, expected_url)
        
        # Test POST with invalid data
        invalid_data = {
            'name': '',  # Invalid: empty name
            'description': 'Updated description',
            'price': 'invalid_price',  # Invalid: not a number
            'image': 'not_a_url',  # Invalid: not a URL
            'category': 'Invalid Category',  # Invalid choice
            'restaurant': self.restaurant.id
        }
        response = self.client.post(
            reverse('dashboard:makanan_update_resto', kwargs={'id': self.menu_item.id}),
            invalid_data
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'update_makanan_resto.html')

    def test_makanan_delete(self):
        self.client.login(username='admin', password='admin123')
        
        response = self.client.post(
            reverse('dashboard:makanan_delete', kwargs={'id': self.menu_item.id})
        )
        self.assertEqual(response.status_code, 302)
        
        # Verify the menu item was deleted
        self.assertFalse(
            MenuItem.objects.filter(id=self.menu_item.id).exists()
        )

    def test_show_json(self):
        response = self.client.get(reverse('dashboard:show_json'))
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('results', data)
        self.assertIn('total_pages', data)
        self.assertIn('current_page', data)
        
        # Test with filters
        response = self.client.get(
            reverse('dashboard:show_json'),
            {'search': 'Test', 'category': 'Makanan Tradisional'}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(len(data['results']) > 0)

    def test_show_json_filters(self):
        """Test JSON endpoint with various filters"""
        # Test price filters
        response = self.client.get(
            reverse('dashboard:show_json'),
            {'min_price': '40000', 'max_price': '60000'}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(
            all(40000 <= float(item['price']) <= 60000 
                for item in data['results'])
        )
        
        # Test kecamatan filter
        response = self.client.get(
            reverse('dashboard:show_json'),
            {'kecamatan': 'Kebayoran Baru'}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(
            all(item['kecamatan'] == 'Kebayoran Baru' 
                for item in data['results'])
        )

    def test_get_reviews(self):
        response = self.client.get(
            reverse('dashboard:menu_item_reviews', 
                   kwargs={'menu_item_id': self.menu_item.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'review_list.html')
        self.assertIn('reviews', response.context)

    def test_get_reviews_resto(self):
        """Test getting reviews from restaurant view"""
        response = self.client.get(
            reverse('dashboard:menu_item_reviews_resto', 
                    kwargs={'menu_item_id': self.menu_item.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'review_list_resto.html')
        self.assertIn('reviews', response.context)
        self.assertEqual(list(response.context['reviews']), [self.review])

    def test_delete_review(self):
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('dashboard:delete_review', 
                   kwargs={'review_id': self.review.id})
        )
        self.assertEqual(response.status_code, 302)
        
        # Verify the review was deleted
        self.assertFalse(
            ReviewEntry.objects.filter(id=self.review.id).exists()
        )

    

    