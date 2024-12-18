from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.forms import ValidationError
from product.models import MenuItem

class ReviewEntry(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name='reviews')
    rating = models.FloatField(
        validators=[MinValueValidator(1.0), MaxValueValidator(5.0)]
    )  # Allows decimal values between 1.0 and 5.0
    review_text = models.TextField()
    review_image = models.ImageField(upload_to='reviews/', null=True, blank=True)
    image_url = models.URLField(max_length=500, null=True, blank=True)  # URL for the review image
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Review by {self.user} on {self.menu_item.name}"
    
    def clean(self):
        super().clean()
        if not (1.0 <= self.rating <= 5.0):
            raise ValidationError("Rating must be between 1.0 and 5.0.")
