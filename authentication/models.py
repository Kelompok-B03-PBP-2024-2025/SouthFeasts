from django.db import models
from django.contrib.auth.models import User
from product.models import MenuItem

# Create your models here.
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=100)
    username = models.CharField(max_length=255)
    fullname= models.CharField(max_length=255)
    country = models.CharField(max_length=255, blank=True) 

    def __str__(self):
        return self.user.username