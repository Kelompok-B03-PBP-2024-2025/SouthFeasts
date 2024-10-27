from decimal import Decimal
from django.forms import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import ReviewEntry
from product.models import MenuItem, Restaurant  # Pastikan `Restaurant` diimport
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()

class ReviewEntryModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="testuser")
        # Buat objek Restaurant
        self.restaurant = Restaurant.objects.create(name="Test Restaurant", location="123 Test St")
        # Tambahkan referensi restaurant ke MenuItem
        self.menu_item = MenuItem.objects.create(name="Test Item", price=10.0, restaurant=self.restaurant)
        
    def test_review_entry_creation(self):
        review = ReviewEntry.objects.create(
            user=self.user,
            menu_item=self.menu_item,
            rating=4.5,
            review_text="Great product!"
        )
        self.assertEqual(review.rating, 4.5)
        self.assertEqual(review.review_text, "Great product!")
        self.assertEqual(review.user, self.user)
        self.assertEqual(review.menu_item, self.menu_item)

    def test_review_entry_rating_validation(self):
        # Coba dengan rating di luar rentang yang diizinkan
        review = ReviewEntry(rating=Decimal('6.0'))  # Misal rating di atas batas
        with self.assertRaises(ValidationError):  # Memastikan ValidationError terpicu
            review.full_clean()  # Menjalankan validasi secara penuh

class AllReviewsViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="testuser")
        # Buat objek Restaurant
        self.restaurant = Restaurant.objects.create(name="Test Restaurant", location="123 Test St")
        # Tambahkan referensi restaurant ke MenuItem
        self.menu_item = MenuItem.objects.create(name="Test Item", price=10.0, restaurant=self.restaurant)
        self.review = ReviewEntry.objects.create(
            user=self.user,
            menu_item=self.menu_item,
            rating=4.5,
            review_text="Great product!"
        )

    def test_all_reviews_view(self):
        response = self.client.get(reverse('review:all_reviews'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Great product!")

    def test_search_reviews_view(self):
        response = self.client.get(reverse('review:all_reviews') + '?search=Great')
        self.assertContains(response, "Great product!")

class CreateReviewViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="12345")
        # Buat objek Restaurant
        self.restaurant = Restaurant.objects.create(name="Test Restaurant", location="123 Test St")
        # Tambahkan referensi restaurant ke MenuItem
        self.menu_item = MenuItem.objects.create(name="Test Item", price=10.0, restaurant=self.restaurant)
        self.client.login(username="testuser", password="12345")

    def test_create_review(self):
        response = self.client.post(reverse('review:create_review', args=[self.menu_item.id]), {
            'review_text': "Great product!",
            'rating': 4.5
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(ReviewEntry.objects.filter(review_text="Great product!").exists())

class EditReviewViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="12345")
        # Buat objek Restaurant
        self.restaurant = Restaurant.objects.create(name="Test Restaurant", location="123 Test St")
        # Tambahkan referensi restaurant ke MenuItem
        self.menu_item = MenuItem.objects.create(name="Test Item", price=10.0, restaurant=self.restaurant)
        self.review = ReviewEntry.objects.create(
            user=self.user,
            menu_item=self.menu_item,
            rating=4.0,
            review_text="Good product"
        )
        self.client.login(username="testuser", password="12345")

    def test_edit_review(self):
        # Simulate editing the review text
        self.review.review_text = "Updated review"
        self.review.save()

        # Refresh the review from the database to check for updated content
        self.review.refresh_from_db()

        # Assert that the updated text is saved correctly
        self.assertEqual(self.review.review_text, "Updated review")


class DeleteReviewViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="staffuser", password="12345", is_staff=True)
        # Buat objek Restaurant
        self.restaurant = Restaurant.objects.create(name="Test Restaurant", location="123 Test St")
        # Tambahkan referensi restaurant ke MenuItem
        self.menu_item = MenuItem.objects.create(name="Test Item", price=10.0, restaurant=self.restaurant)
        self.review = ReviewEntry.objects.create(
            user=self.user,
            menu_item=self.menu_item,
            rating=4.0,
            review_text="Good product"
        )
        self.client.login(username="staffuser", password="12345")

    def test_delete_review(self):
        response = self.client.post(reverse('review:delete_review', args=[self.review.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(ReviewEntry.objects.filter(id=self.review.id).exists())
