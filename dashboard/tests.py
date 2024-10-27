# dashboard/tests.py
from django.http import HttpResponseRedirect
from dashboard.views import remove_empty_restaurants
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
        
        # Buat user test
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Buat profil user
        self.profile = UserProfile.objects.create(
            user=self.user,
            user_type='USER',
            username='testuser',
            fullname='Test User',
            country='Indonesia'
        )
        
        # Buat admin test
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
        
        # Buat restoran test
        self.restaurant = Restaurant.objects.create(
            name='Test Restaurant',
            city='Jakarta',
            kecamatan='Kebayoran Baru',
            location='Test Location'
        )
        
        # Buat menu item test
        self.menu_item = MenuItem.objects.create(
            name='Test Food',
            image='http://example.com/food.jpg',
            description='Test description',
            category='Makanan Tradisional',
            price=Decimal('50000.00'),
            restaurant=self.restaurant
        )
        
        # Buat menu item lain untuk pengujian pencarian
        self.menu_item2 = MenuItem.objects.create(
            name='Special Nasi Goreng',
            image='http://example.com/food2.jpg',
            description='Another test description',
            category='Makanan Tradisional',
            price=Decimal('45000.00'),
            restaurant=self.restaurant
        )
        
        # Buat review test
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
        
        # Periksa apakah admin user dibuat dengan benar
        admin = User.objects.get(username='admin')
        self.assertTrue(admin.is_staff)
        self.assertEqual(admin.userprofile.user_type, 'ADMIN')

    def test_makanan_list(self):
        response = self.client.get(reverse('dashboard:makanan_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'makanan_list.html')
        
        # Uji dengan filter
        response = self.client.get(
            reverse('dashboard:makanan_list'),
            {'category': 'Makanan Tradisional', 'kecamatan': 'Kebayoran Baru'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('makanans', response.context)

        # Uji filter harga minimum
        response = self.client.get(
            reverse('dashboard:makanan_list'),
            {'min_price': '40000'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(makanan['price'] >= 40000 for makanan in response.context['makanans']))

        # Uji filter harga maksimum
        response = self.client.get(
            reverse('dashboard:makanan_list'),
            {'max_price': '60000'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(all(makanan['price'] <= 60000 for makanan in response.context['makanans']))

        # Uji filter harga minimum dan maksimum
        response = self.client.get(
            reverse('dashboard:makanan_list'),
            {'min_price': '40000', 'max_price': '60000'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            all(40000 <= makanan['price'] <= 60000 
                for makanan in response.context['makanans'])
        )
        # Uji filter pencarian
        # Uji pencocokan tepat
        response = self.client.get(
            reverse('dashboard:makanan_list'),
            {'search': 'Test Food'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('makanans', response.context)
        makanans = response.context['makanans']
        self.assertTrue(any(m['item'] == 'Test Food' for m in makanans))
        self.assertFalse(any(m['item'] == 'Special Nasi Goreng' for m in makanans))

        # Uji pencocokan sebagian
        response = self.client.get(
            reverse('dashboard:makanan_list'),
            {'search': 'Nasi'}
        )
        self.assertEqual(response.status_code, 200)
        makanans = response.context['makanans']
        self.assertTrue(any(m['item'] == 'Special Nasi Goreng' for m in makanans))
        self.assertFalse(any(m['item'] == 'Test Food' for m in makanans))

        # Uji pencocokan tidak sensitif huruf besar/kecil
        response = self.client.get(
            reverse('dashboard:makanan_list'),
            {'search': 'test'}
        )
        self.assertEqual(response.status_code, 200)
        makanans = response.context['makanans']
        self.assertTrue(any(m['item'] == 'Test Food' for m in makanans))

        # Uji tidak ada pencocokan
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
        
        # Uji restoran yang tidak ada
        response = self.client.get(
            reverse('dashboard:restaurant_menu', 
                   kwargs={'resto_name': 'NonExistentRestaurant'})
        )
        self.assertEqual(response.status_code, 404)

    def test_restaurant_list(self):
        response = self.client.get(reverse('dashboard:restaurant_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'resto_list.html')
        
        # Uji dengan filter
        response = self.client.get(
            reverse('dashboard:restaurant_list'),
            {'kecamatan': 'Kebayoran Baru', 'search': 'Test'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('restaurants', response.context)

    def test_restaurant_update_form(self):
        """Uji fungsi pembaruan restoran"""
        self.client.login(username='admin', password='admin123')
        
        # Uji permintaan GET
        response = self.client.get(
            reverse('dashboard:restaurant_update', 
                    kwargs={'resto_name': self.restaurant.name})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'update_restaurant.html')
        
        # Uji POST dengan data valid
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
        
        # Uji POST dengan data tidak valid
        invalid_data = {
            'name': '',  # Tidak valid: nama kosong
            'city': 'Jakarta',
            'kecamatan': 'Invalid Kecamatan',  # Pilihan tidak valid
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
        
        # Verifikasi menu item dibuat
        self.assertTrue(
            MenuItem.objects.filter(name='New Food').exists()
        )

    def test_makanan_create_invalid(self):
        """Uji pembuatan makanan dengan data tidak valid"""
        self.client.login(username='admin', password='admin123')
        
        # Uji dengan data tidak valid
        invalid_data = {
            'name': '',  # Tidak valid: nama kosong
            'description': 'Test description',
            'price': 'invalid_price',  # Tidak valid: bukan angka
            'image': 'not_a_url',  # Tidak valid: bukan URL
            'category': 'Invalid Category',  # Pilihan tidak valid
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
        
        # Uji permintaan GET - harus menampilkan form
        response = self.client.get(
            reverse('dashboard:makanan_update', kwargs={'id': self.menu_item.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'update_makanan.html')
        
        # Uji permintaan POST dengan data valid
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
        # Periksa status respons langsung 
        self.assertEqual(response.status_code, 302)
        # Konfirmasi URL redirect sesuai 
        self.assertRedirects(response, expected_url) 
        
        # Verifikasi menu item diperbarui terlepas dari jenis respons
        updated_item = MenuItem.objects.get(id=self.menu_item.id)
        if response.status_code == 302:  # Hanya periksa jika pembaruan berhasil
            self.assertEqual(updated_item.name, 'Updated Food')
            self.assertEqual(updated_item.description, 'Updated description')
        
        # Uji permintaan POST dengan data tidak valid
        invalid_data = {
            'name': '',  # Tidak valid: nama kosong
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
        self.assertEqual(response.status_code, 200)  # Harus menampilkan form dengan error
        self.assertTemplateUsed(response, 'update_makanan.html')

    def test_makanan_update_resto(self):
        """Uji pembaruan menu item dari tampilan restoran"""
        self.client.login(username='admin', password='admin123')
        
        # Uji permintaan GET
        response = self.client.get(
            reverse('dashboard:makanan_update_resto', kwargs={'id': self.menu_item.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'update_makanan_resto.html')
        
        # Uji POST dengan data valid
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
                
        # Periksa status respons langsung
        self.assertEqual(response.status_code, 302)

        # Konfirmasi URL redirect sesuai
        self.assertRedirects(response, expected_url)
        
        # Uji POST dengan data tidak valid
        invalid_data = {
            'name': '',  # Tidak valid: nama kosong
            'description': 'Updated description',
            'price': 'invalid_price',  # Tidak valid: bukan angka
            'image': 'not_a_url',  # Tidak valid: bukan URL
            'category': 'Invalid Category',  # Pilihan tidak valid
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
        
        # Verifikasi menu item dihapus
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
        
        # Uji dengan filter
        response = self.client.get(
            reverse('dashboard:show_json'),
            {'search': 'Test', 'category': 'Makanan Tradisional'}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(len(data['results']) > 0)

    def test_show_json_filters(self):
        """Uji endpoint JSON dengan berbagai filter"""
        # Uji filter harga
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
        
        # Uji filter kecamatan
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
        """Uji mendapatkan review dari tampilan restoran"""
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
        
        # Verifikasi review dihapus
        self.assertFalse(
            ReviewEntry.objects.filter(id=self.review.id).exists()
        )
    
    def test_show_json_restaurant(self):
        """Test show_json_restaurant endpoint dengan filters"""
        # Test basic response
        response = self.client.get(reverse('dashboard:show_json_restaurant'))
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('restaurants', data)
        self.assertIn('kecamatans', data)
        self.assertIn('total_pages', data)
        self.assertIn('current_page', data)
        
        # Test search filter
        response = self.client.get(
            reverse('dashboard:show_json_restaurant'),
            {'search': 'Test Restaurant'}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(
            any(r['name'] == 'Test Restaurant' 
                for r in data['restaurants'])
        )
        
        # Test kecamatan filter
        response = self.client.get(
            reverse('dashboard:show_json_restaurant'),
            {'kecamatan': 'Kebayoran Baru'}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(
            all(r['kecamatan'] == 'Kebayoran Baru' 
                for r in data['restaurants'])
        )
        
        # Test search and kecamatan filters
        response = self.client.get(
            reverse('dashboard:show_json_restaurant'),
            {'search': 'Test', 'kecamatan': 'Kebayoran Baru'}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        filtered_restaurants = data['restaurants']
        self.assertTrue(all(
            r['name'].lower().find('test') != -1 and 
            r['kecamatan'] == 'Kebayoran Baru'
            for r in filtered_restaurants
        ))
        
        # Verifikasi data yang dikembalikan
        if data['restaurants']:
            restaurant = data['restaurants'][0]
            expected_fields = {
                'id', 'name', 'kecamatan', 'location', 
                'menu_count', 'min_price', 'max_price', 'image'
            }
            self.assertEqual(set(restaurant.keys()), expected_fields)

    def test_remove_empty_restaurants(self):
        """Test untuk fungsi remove_empty_restaurants"""
        # Buat restoran kosong
        empty_restaurant = Restaurant.objects.create(
            name='Empty Restaurant',
            city='Jakarta',
            kecamatan='Kebayoran Baru',
            location='Empty Location'
        )
        
        # Buat restoran dengan menu item (sudah ada dari setUp)
        self.assertTrue(Restaurant.objects.filter(
            name='Empty Restaurant').exists())
        self.assertTrue(Restaurant.objects.filter(
            name='Test Restaurant').exists())
        
        # Run function 
        remove_empty_restaurants()
        
        # Verifikasi restoran kosong dihapus
        self.assertFalse(Restaurant.objects.filter(
            name='Empty Restaurant').exists())
        
        # Verifikasi restoran dengan menu item tetap ada
        self.assertTrue(Restaurant.objects.filter(
            name='Test Restaurant').exists())
        
        # Verify jumlah restoran
        self.assertEqual(Restaurant.objects.count(), 1)

        

        