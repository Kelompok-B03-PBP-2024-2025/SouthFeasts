from django.urls import path, include
from . import views

app_name = 'wishlist'

urlpatterns = [
   path('json/', views.show_json, name='show-json'),
    # Collection URLs
    path('', views.collection_list, name='collection-list'),
    path('collection/add/', views.collection_add, name='collection-add'),
    path('collection/<int:collection_id>/', views.collection_detail, name='collection-detail'),
    path('collection/<int:collection_id>/edit/', views.collection_edit, name='collection-edit'),
    path('collection/<int:collection_id>/delete/', views.collection_delete, name='collection-delete'),
    path('collection/<int:collection_id>/set-default/', views.collection_set_default, name='collection-set-default'),
    path('get-collections/', views.get_collections, name='get-collections'),
    path('create-collection-ajax/', views.create_collection_ajax, name='create-collection-ajax'),
    
    # Item URLs
    path('create/', views.add_to_wishlist_from_menu, name='create'),
    path('item/add/<int:menu_item_id>/', views.item_add, name='item-add'),
    path('item/<int:item_id>/remove/', views.item_remove, name='item-remove'),
    path('item/<int:item_id>/move/<int:collection_id>/', views.item_move, name='item-move'),
    path('item/<int:item_id>/add-to/<int:collection_id>/', views.add_item_to_collection, name='add-item-to-collection'),
    path('product/', include('product.urls', namespace='product')),

    # Flutter
    path('flutter/collections/', views.get_collections_flutter, name='flutter-collections'),
    path('flutter/collections/create/', views.create_collection_flutter, name='flutter-create-collection'),
    # path('flutter/collections/create/', views.create_collection_flutter, name='flutter-create-collection'),
    path('flutter/collections/<int:collection_id>/delete/', views.delete_collection_flutter, name='flutter-delete-collection'),
    path('flutter/wishlist/add/', views.add_to_wishlist_flutter, name='flutter-add-wishlist'),
    path('flutter/wishlist/<int:item_id>/remove/', views.remove_from_wishlist_flutter, name='flutter-remove-wishlist'),
    path('flutter/wishlist/move/', views.move_item_flutter, name='flutter-move-item'),
    path('flutter/collections/default/', views.get_default_collection, name='flutter-default-collection'),
    ]