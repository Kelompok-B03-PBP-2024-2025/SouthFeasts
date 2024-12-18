from django.conf import settings
from django.db import models
from django.urls import reverse

class Restaurant(models.Model):
    KECAMATAN_CHOICE = [
        ("Kebayoran Lama", "Kebayoran Lama"),
        ("Kebayoran Baru", "Kebayoran Baru"),
        ("Cilandak", "Cilandak"),
        ("Mampang Prapatan", "Mampang Prapatan"),
        ("Jagakarsa","Jagakarsa"),        
        ("Pancoran", "Pancoran"),
        ("Pasar Minggu", "Pasar Minggu"),
        ("Pesanggrahan", "Pesanggrahan"),
        ("Setiabudi", "Setiabudi"),
        ("Tebet", "Tebet"),
    ]
    name = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    kecamatan = models.CharField(max_length=100, choices=KECAMATAN_CHOICE)
    location = models.TextField(help_text="Detailed address of the restaurant")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('restaurant-detail', kwargs={'pk': self.pk})
    
class Reservation(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    date = models.DateTimeField()
