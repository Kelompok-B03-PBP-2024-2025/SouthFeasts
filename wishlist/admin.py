from django.contrib import admin
from .models import WishlistCollection, WishlistItem

@admin.register(WishlistCollection)
class WishlistCollectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'description', 'is_default')
    list_filter = ('user', 'is_default')
    search_fields = ('name', 'user__username')
    
    def get_readonly_fields(self, request, obj=None):
        # Prevent changing is_default for existing collections
        if obj:
            return ('is_default',)
        return ()

@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ('menu_item', 'collection', 'created_at')
    list_filter = ('collection__user', 'collection', 'menu_item')
    search_fields = ('menu_item__name', 'collection__name')