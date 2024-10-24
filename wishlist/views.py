from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Q
from .models import WishlistCollection, WishlistItem
from .forms import WishlistCollectionForm
from product.models import MenuItem

@login_required
def collection_list(request):
    collections = WishlistCollection.objects.filter(user=request.user)
    
    # Ensure "All Wishlist" collection exists
    all_wishlist = collections.filter(name="All Wishlist").first()
    if not all_wishlist:
        WishlistCollection.objects.create(
            user=request.user,
            name="All Wishlist",
            description="All your wishlisted items in one place",
            is_default=True
        )
        # Refresh collections queryset
        collections = WishlistCollection.objects.filter(user=request.user)
        
    return render(request, 'collections.html', {
        'collections': collections
    })

@login_required
def collection_add(request):
    if request.method == 'POST':
        form = WishlistCollectionForm(request.POST)
        if form.is_valid():
            collection = form.save(commit=False)
            collection.user = request.user
            collection.save()
            return redirect('wishlist:collection-list')
    else:
        form = WishlistCollectionForm()
    
    return render(request, 'create_collection.html', {
        'form': form,
        'is_add': True
    })

@login_required
def collection_detail(request, collection_id):
    collection = get_object_or_404(WishlistCollection, id=collection_id, user=request.user)
    
    if collection.name == "All Wishlist":
        # Get all items from all collections for this user
        all_items = WishlistItem.objects.filter(
            collection__user=request.user
        ).select_related('menu_item').distinct('menu_item')
    else:
        all_items = collection.items.all()
        
    return render(request, 'collection_detail.html', {
        'collection': collection,
        'items': all_items
    })

@login_required
def collection_edit(request, collection_id):
    collection = get_object_or_404(WishlistCollection, id=collection_id, user=request.user)
    
    # Prevent editing All Wishlist collection
    if collection.name == "All Wishlist":
        return redirect('wishlist:collection-detail', collection_id=collection.id)
    
    if request.method == 'POST':
        form = WishlistCollectionForm(request.POST, instance=collection)
        if form.is_valid():
            form.save()
            return redirect('wishlist:collection-detail', collection_id=collection_id)
    else:
        form = WishlistCollectionForm(instance=collection)
    
    return render(request, 'edit_collection.html', {
        'form': form,
        'collection': collection,
        'is_add': False
    })

@login_required
def collection_delete(request, collection_id):
    collection = get_object_or_404(WishlistCollection, id=collection_id, user=request.user)
    
    # Prevent deletion of "All Wishlist"
    if collection.name == "All Wishlist":
        return JsonResponse({
            'status': 'error',
            'message': 'Cannot delete All Wishlist collection'
        }, status=400)
        
    if request.method == 'POST':
        collection.delete()
        return redirect('wishlist:collection-list')
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def collection_set_default(request, collection_id):
    collection = get_object_or_404(WishlistCollection, id=collection_id, user=request.user)
    
    # Prevent setting All Wishlist as default
    if collection.name == "All Wishlist":
        return JsonResponse({
            'status': 'error',
            'message': 'Cannot set All Wishlist as default'
        }, status=400)
        
    if request.method == 'POST':
        with transaction.atomic():
            # Remove default from other collections
            WishlistCollection.objects.filter(user=request.user, is_default=True).update(is_default=False)
            # Set this collection as default
            collection.is_default = True
            collection.save()
        
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def item_add(request, menu_item_id):
    if request.method == 'POST':
        collection_id = request.POST.get('collection_id')
        collection = get_object_or_404(WishlistCollection, id=collection_id, user=request.user)
        menu_item = get_object_or_404(MenuItem, id=menu_item_id)
        
        # Don't allow adding directly to All Wishlist
        if collection.name == "All Wishlist":
            return JsonResponse({
                'status': 'error',
                'message': 'Cannot add items directly to All Wishlist'
            }, status=400)
        
        if not WishlistItem.objects.filter(collection=collection, menu_item=menu_item).exists():
            WishlistItem.objects.create(collection=collection, menu_item=menu_item)
            return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'exists'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def item_remove(request, item_id):
    if request.method == 'POST':
        item = get_object_or_404(WishlistItem, id=item_id, collection__user=request.user)
        # When removing from All Wishlist, remove from all collections
        if item.collection.name == "All Wishlist":
            WishlistItem.objects.filter(
                collection__user=request.user,
                menu_item=item.menu_item
            ).delete()
        else:
            item.delete()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def item_move(request, item_id, collection_id):
    if request.method == 'POST':
        item = get_object_or_404(WishlistItem, id=item_id, collection__user=request.user)
        new_collection = get_object_or_404(WishlistCollection, id=collection_id, user=request.user)
        
        # Don't allow moving to All Wishlist
        if new_collection.name == "All Wishlist":
            return JsonResponse({
                'status': 'error',
                'message': 'Cannot move items to All Wishlist'
            }, status=400)
        
        # Don't allow moving from All Wishlist
        if item.collection.name == "All Wishlist":
            return JsonResponse({
                'status': 'error',
                'message': 'Cannot move items from All Wishlist'
            }, status=400)
        
        if not WishlistItem.objects.filter(collection=new_collection, menu_item=item.menu_item).exists():
            item.collection = new_collection
            item.save()
            return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'exists'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def add_to_wishlist_from_menu(request):
    menu_item_id = request.GET.get('menu_item')
    if not menu_item_id:
        return redirect('menu:catalog')
        
    # Get or create default collection
    default_collection = WishlistCollection.objects.filter(
        user=request.user,
        is_default=True
    ).exclude(name="All Wishlist").first()
    
    if not default_collection:
        default_collection = WishlistCollection.objects.create(
            user=request.user,
            name="My Wishlist",
            is_default=True
        )
    
    menu_item = get_object_or_404(MenuItem, id=menu_item_id)
    
    # Add to default collection
    WishlistItem.objects.get_or_create(
        collection=default_collection,
        menu_item=menu_item
    )
    
    if request.GET.get('next'):
        return redirect(request.GET.get('next'))
    return redirect('wishlist:collection-detail', collection_id=default_collection.id)