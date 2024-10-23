from django.urls import path
from . import views

app_name = 'wishlist'

urlpatterns = [
    # Collection URLs
    path('', views.collection_list, name='collection-list'),
    path('collection/add/', views.collection_add, name='collection-add'),
    path('collection/<int:collection_id>/', views.collection_detail, name='collection-detail'),
    path('collection/<int:collection_id>/edit/', views.collection_edit, name='collection-edit'),
    path('collection/<int:collection_id>/delete/', views.collection_delete, name='collection-delete'),
    path('collection/<int:collection_id>/set-default/', views.collection_set_default, name='collection-set-default'),

    # Item URLs
    path('create/', views.add_to_wishlist_from_menu, name='create'),
    path('item/add/<int:menu_item_id>/', views.item_add, name='item-add'),
    path('item/<int:item_id>/remove/', views.item_remove, name='item-remove'),
    path('item/<int:item_id>/move/<int:collection_id>/', views.item_move, name='item-move'),
]