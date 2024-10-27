# product/tests.py
from django.test import TestCase, Client
from django.urls import reverse
from decimal import Decimal
from django.contrib.auth.models import User
from .models import MenuItem 
from restaurant.models import Restaurant
from review.models import ReviewEntry
from wishlist.models import WishlistItem, WishlistCollection
import json
import pandas as pd
import os

class MenuItemModelTest(TestCase):
    def setUp(self):
        self.restaurant = Restaurant.objects.create(
            name="Test Restaurant",
            city="Jakarta",
            kecamatan="Tebet",
            location="Test Location"
        )
        self.menu_item = MenuItem.objects.create(
            name="Test Menu",
            image="http://test.com/image.jpg",
            description="Test Description",
            category="Makanan Laut",
            price=Decimal('50000.00'),
            restaurant=self.restaurant
        )

    def test_menu_item_str(self):
        self.assertEqual(str(self.menu_item), "Test Menu at Test Restaurant")

    def test_menu_item_get_absolute_url(self):
        url = self.menu_item.get_absolute_url()
        self.assertEqual(url, f'/product/{self.menu_item.id}/')

    def test_menu_item_fields(self):
        self.assertEqual(self.menu_item.name, "Test Menu")
        self.assertEqual(self.menu_item.price, Decimal('50000.00'))
        self.assertEqual(self.menu_item.category, "Makanan Laut")
        self.assertEqual(self.menu_item.restaurant, self.restaurant)

class RestaurantModelTest(TestCase):
    def setUp(self):
        self.restaurant = Restaurant.objects.create(
            name="Test Restaurant",
            city="Jakarta",
            kecamatan="Tebet",
            location="Test Location"
        )

    def test_restaurant_str(self):
        self.assertEqual(str(self.restaurant), "Test Restaurant")

    def test_restaurant_fields(self):
        self.assertEqual(self.restaurant.city, "Jakarta")
        self.assertEqual(self.restaurant.kecamatan, "Tebet")
        self.assertEqual(self.restaurant.location, "Test Location")

class MenuCatalogViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.restaurant = Restaurant.objects.create(
            name="Test Restaurant",
            city="Jakarta",
            kecamatan="Tebet",
            location="Test Location"
        )
        self.menu_item = MenuItem.objects.create(
            name="Test Menu",
            image="http://test.com/image.jpg",
            description="Test Description",
            category="Makanan Laut",
            price=Decimal('50000.00'),
            restaurant=self.restaurant
        )
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_menu_catalog_GET(self):
        response = self.client.get(reverse('product:menu_catalog'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'menu_catalog.html')
        self.assertIn('menu_items', response.context)

    def test_menu_catalog_search(self):
        response = self.client.get(
            reverse('product:menu_catalog'),
            {'search': 'Test'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.menu_item, response.context['menu_items'])

    def test_menu_catalog_category_filter(self):
        response = self.client.get(
            reverse('product:menu_catalog'),
            {'category': 'Makanan Laut'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.menu_item, response.context['menu_items'])

    def test_menu_catalog_price_filter(self):
        response = self.client.get(
            reverse('product:menu_catalog'),
            {'min_price': '40000', 'max_price': '60000'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.menu_item, response.context['menu_items'])

    def test_menu_catalog_location_filter(self):
        response = self.client.get(
            reverse('product:menu_catalog'),
            {'kecamatan': 'Tebet'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.menu_item, response.context['menu_items'])

    def test_menu_catalog_with_authenticated_user(self):
        self.client.login(username='testuser', password='testpass123')
        collection = WishlistCollection.objects.create(user=self.user)
        WishlistItem.objects.create(
            collection=collection,
            menu_item=self.menu_item
        )
        response = self.client.get(reverse('product:menu_catalog'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['menu_items'][0].is_in_wishlist)

class MenuDetailViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.restaurant = Restaurant.objects.create(
            name="Test Restaurant",
            city="Jakarta",
            kecamatan="Tebet",
            location="Test Location"
        )
        self.menu_item = MenuItem.objects.create(
            name="Test Menu",
            image="http://test.com/image.jpg",
            description="Test Description",
            category="Makanan Laut",
            price=Decimal('50000.00'),
            restaurant=self.restaurant
        )
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.review = ReviewEntry.objects.create(
            user=self.user,
            menu_item=self.menu_item,
            rating=5.0,
            review_text ="Great food!"
        )

    def test_menu_detail_GET(self):
        response = self.client.get(
            reverse('product:menu_detail', args=[self.menu_item.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'menu_detail.html')
        self.assertEqual(response.context['menu_item'], self.menu_item)

    def test_menu_detail_404(self):
        response = self.client.get(
            reverse('product:menu_detail', args=[99999])
        )
        self.assertEqual(response.status_code, 404)

    def test_menu_detail_with_reviews(self):
        response = self.client.get(
            reverse('product:menu_detail', args=[self.menu_item.id])
        )
        self.assertIn(self.review, response.context['reviews'])

    def test_menu_detail_wishlist_status_authenticated(self):
        self.client.login(username='testuser', password='testpass123')
        collection = WishlistCollection.objects.create(user=self.user)
        WishlistItem.objects.create(
            collection=collection,
            menu_item=self.menu_item
        )
        response = self.client.get(
            reverse('product:menu_detail', args=[self.menu_item.id])
        )
        self.assertTrue(response.context['menu_item'].is_in_wishlist)

    def test_menu_detail_wishlist_status_unauthenticated(self):
        response = self.client.get(
            reverse('product:menu_detail', args=[self.menu_item.id])
        )
        self.assertFalse(response.context['menu_item'].is_in_wishlist)

class RestaurantMenuViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.restaurant = Restaurant.objects.create(
            name="Test Restaurant",
            city="Jakarta",
            kecamatan="Tebet",
            location="Test Location"
        )
        self.menu_item = MenuItem.objects.create(
            name="Test Menu",
            image="http://test.com/image.jpg",
            description="Test Description",
            category="Makanan Laut",
            price=Decimal('50000.00'),
            restaurant=self.restaurant
        )

    def test_restaurant_menu_GET(self):
        response = self.client.get(
            reverse('product:restaurant_menu', args=[self.restaurant.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'restaurant_menu.html')
        self.assertEqual(response.context['restaurant'], self.restaurant)
        self.assertIn(self.menu_item, response.context['menu_items'])

    def test_restaurant_menu_404(self):
        response = self.client.get(
            reverse('product:restaurant_menu', args=[99999])
        )
        self.assertEqual(response.status_code, 404)
    

