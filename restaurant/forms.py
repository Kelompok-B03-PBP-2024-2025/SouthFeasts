<<<<<<< HEAD
from django import forms
from .models import Reservation
from datetime import datetime

class ReservationForm(forms.ModelForm):
    reservation_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text='Select date for your reservation'
    )
    reservation_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time'}),
        help_text='Select time for your reservation'
    )
    number_of_people = forms.IntegerField(
        min_value=1,
        max_value=20,
        initial=1,
        help_text='Number of people for reservation'
    )

    class Meta:
        model = Reservation
        fields = ['restaurant', 'reservation_date', 'reservation_time', 'number_of_people']
    
    def clean(self):
        cleaned_data = super().clean()
        reservation_date = cleaned_data.get('reservation_date')
        reservation_time = cleaned_data.get('reservation_time')
        
        if reservation_date and reservation_time:
            reservation_datetime = datetime.combine(reservation_date, reservation_time)
            if reservation_datetime < datetime.now():
                raise forms.ValidationError("Reservation date and time cannot be in the past!")
        
        return cleaned_data
=======
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone

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
    reservation_date = models.DateField(null=True)
    reservation_time = models.TimeField(null=True)
    number_of_people = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
>>>>>>> 5e761cf10298945f6d8acba7de1dea91aea869ca
