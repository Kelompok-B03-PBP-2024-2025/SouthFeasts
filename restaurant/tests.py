# tests.py
from django.test import TestCase, Client
from django.urls import reverse
from restaurant.models import Restaurant
from product.models import MenuItem
from decimal import Decimal

class RestaurantTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create base test restaurant for model tests
        cls.restaurant = Restaurant.objects.create(
            name='Test Restaurant',
            city='Jakarta',
            kecamatan='Tebet',
            location='Jl. Test No. 123'
        )
        
        # Create menu items for the restaurant
        cls.menu_item = MenuItem.objects.create(
            name='Test Item',
            image='http://example.com/image.jpg',
            description='Test Description',
            category='Makanan Laut',
            price=Decimal('50000.00'),
            restaurant=cls.restaurant
        )
        
        # Create additional restaurants for pagination testing
        for i in range(14):  # Creates 14 more restaurants (total 15)
            Restaurant.objects.create(
                name=f'Restaurant {i}',
                city='Jakarta',
                kecamatan='Tebet' if i % 2 == 0 else 'Cilandak',
                location=f'Location {i}'
            )
            
        # Create additional menu items for filtering tests
        for i in range(4):
            MenuItem.objects.create(
                name=f'Menu Item {i}',
                image='http://example.com/image.jpg',
                description=f'Description {i}',
                category='Makanan Tradisional' if i % 2 == 0 else 'Makanan Sehat',
                price=Decimal(f'{(i+1)*10000}.00'),
                restaurant=cls.restaurant
            )

    def setUp(self):
        self.client = Client()

    # Model Tests
    def test_restaurant_model(self):
        """Test Restaurant model methods and fields"""
        self.assertEqual(self.restaurant.name, 'Test Restaurant')
        self.assertEqual(self.restaurant.city, 'Jakarta')
        self.assertEqual(self.restaurant.kecamatan, 'Tebet')
        self.assertEqual(self.restaurant.location, 'Jl. Test No. 123')
        self.assertEqual(str(self.restaurant), 'Test Restaurant')
        expected_url = reverse('restaurant:restaurant_detail', kwargs={'pk': self.restaurant.pk})
        self.assertEqual(self.restaurant.get_absolute_url(), expected_url)

    def test_menu_item_model(self):
        """Test MenuItem model methods and fields"""
        self.assertEqual(self.menu_item.name, 'Test Item')
        self.assertEqual(self.menu_item.image, 'http://example.com/image.jpg')
        self.assertEqual(self.menu_item.description, 'Test Description')
        self.assertEqual(self.menu_item.category, 'Makanan Laut')
        self.assertEqual(self.menu_item.price, Decimal('50000.00'))
        self.assertEqual(self.menu_item.restaurant, self.restaurant)
        self.assertEqual(str(self.menu_item), 'Test Item at Test Restaurant')
        expected_url = reverse('product:menu_detail', kwargs={'id': self.menu_item.id})
        self.assertEqual(self.menu_item.get_absolute_url(), expected_url)

    # Restaurant List View Tests
    def test_restaurant_list_basic(self):
        """Test basic restaurant list view functionality"""
        response = self.client.get(reverse('restaurant:restaurant_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'restaurant_list.html')
        # Test pagination (12 per page)
        self.assertEqual(len(response.context['restaurants'].object_list), 12)
        self.assertTrue(response.context['restaurants'].has_next())

    def test_restaurant_list_pagination(self):
        """Test restaurant list pagination"""
        # Test first page
        response = self.client.get(reverse('restaurant:restaurant_list'))
        self.assertEqual(len(response.context['restaurants'].object_list), 12)
        
        # Test second page
        response = self.client.get(reverse('restaurant:restaurant_list'), {'page': 2})
        self.assertEqual(len(response.context['restaurants'].object_list), 3)
        self.assertTrue(response.context['restaurants'].has_previous())
        self.assertFalse(response.context['restaurants'].has_next())

    def test_restaurant_list_search(self):
        """Test restaurant list search functionality"""
        # Test exact name search
        response = self.client.get(reverse('restaurant:restaurant_list'), {'search': 'Test Restaurant'})
        self.assertEqual(len(response.context['restaurants']), 1)
        self.assertEqual(response.context['restaurants'][0].name, 'Test Restaurant')
        
        # Test partial name search
        response = self.client.get(reverse('restaurant:restaurant_list'), {'search': 'Restaurant'})
        self.assertTrue(len(response.context['restaurants']) > 1)
        
        # Test location search
        response = self.client.get(reverse('restaurant:restaurant_list'), {'search': 'Location'})
        self.assertTrue(len(response.context['restaurants']) > 0)

    def test_restaurant_list_kecamatan_filter(self):
        """Test restaurant list kecamatan filter"""
        response = self.client.get(reverse('restaurant:restaurant_list'), {'kecamatan': 'Tebet'})
        self.assertEqual(response.status_code, 200)
        for restaurant in response.context['restaurants']:
            self.assertEqual(restaurant.kecamatan, 'Tebet')
        
        # Test different kecamatan
        response = self.client.get(reverse('restaurant:restaurant_list'), {'kecamatan': 'Cilandak'})
        self.assertEqual(response.status_code, 200)
        for restaurant in response.context['restaurants']:
            self.assertEqual(restaurant.kecamatan, 'Cilandak')

    # Restaurant Detail View Tests
    def test_restaurant_detail_basic(self):
        """Test basic restaurant detail view functionality"""
        response = self.client.get(reverse('restaurant:restaurant_detail', kwargs={'pk': self.restaurant.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'restaurant_detail.html')
        self.assertEqual(response.context['restaurant'], self.restaurant)
        self.assertTrue(len(response.context['menu_items']) > 0)

    def test_restaurant_detail_invalid_id(self):
        """Test restaurant detail view with invalid id"""
        response = self.client.get(reverse('restaurant:restaurant_detail', kwargs={'pk': 9999}))
        self.assertEqual(response.status_code, 404)

    def test_restaurant_detail_category_filter(self):
        """Test restaurant detail view category filter"""
        # Test Makanan Laut category
        response = self.client.get(
            reverse('restaurant:restaurant_detail', kwargs={'pk': self.restaurant.pk}),
            {'category': 'Makanan Laut'}
        )
        self.assertEqual(response.status_code, 200)
        for menu_item in response.context['menu_items']:
            self.assertEqual(menu_item.category, 'Makanan Laut')
        
        # Test Makanan Tradisional category
        response = self.client.get(
            reverse('restaurant:restaurant_detail', kwargs={'pk': self.restaurant.pk}),
            {'category': 'Makanan Tradisional'}
        )
        self.assertEqual(response.status_code, 200)
        for menu_item in response.context['menu_items']:
            self.assertEqual(menu_item.category, 'Makanan Tradisional')

    def test_restaurant_detail_price_filter(self):
        """Test restaurant detail view price filter"""
        # Test min price filter
        response = self.client.get(
            reverse('restaurant:restaurant_detail', kwargs={'pk': self.restaurant.pk}),
            {'min_price': '20000'}
        )
        self.assertEqual(response.status_code, 200)
        for menu_item in response.context['menu_items']:
            self.assertTrue(float(menu_item.price) >= 20000)

        # Test max price filter
        response = self.client.get(
            reverse('restaurant:restaurant_detail', kwargs={'pk': self.restaurant.pk}),
            {'max_price': '30000'}
        )
        self.assertEqual(response.status_code, 200)
        for menu_item in response.context['menu_items']:
            self.assertTrue(float(menu_item.price) <= 30000)

        # Test price range filter
        response = self.client.get(
            reverse('restaurant:restaurant_detail', kwargs={'pk': self.restaurant.pk}),
            {'min_price': '20000', 'max_price': '40000'}
        )
        self.assertEqual(response.status_code, 200)
        for menu_item in response.context['menu_items']:
            self.assertTrue(20000 <= float(menu_item.price) <= 40000)