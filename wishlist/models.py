from django.db import models
from django.contrib.auth.models import User
from product.models import MenuItem
from django.utils import timezone

# buat per collection nya
class WishlistCollection(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='wishlist_collections'
    )
    description = models.TextField(blank=True, null=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        unique_together = ['user', 'name']  

    def __str__(self):
        return f"{self.name} - {self.user.username}'s Collection"
    
    def save(self, *args, **kwargs):
        # Ensure each user has one default collection
        if self.is_default:
            WishlistCollection.objects.filter(
                user=self.user,
                is_default=True
            ).exclude(id=self.id).update(is_default=False)
        super().save(*args, **kwargs)

class WishlistItem(models.Model):
    collection = models.ForeignKey(
        WishlistCollection,
        on_delete=models.CASCADE,
        related_name='items'
    )
    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.CASCADE,
        related_name='wishlist_items'
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ['collection', 'menu_item']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.menu_item.name} in {self.collection.name}"
