# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Q
from .models import WishlistCollection, WishlistItem
from .forms import WishlistCollectionForm
from product.models import MenuItem
import json
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.html import strip_tags

@login_required
def collection_list(request):
    # Get all collections except "All Wishlist"
    collections = WishlistCollection.objects.filter(user=request.user).exclude(name="All Wishlist")
    
    # Cek apakah sudah ada koleksi default
    default_collection = collections.filter(is_default=True).first()
    if not default_collection:
        try:
            default_collection = WishlistCollection.objects.get(
                user=request.user,
                name="My Wishlist"
            )
            # Jika ada tapi bukan default, jadikan default
            if not default_collection.is_default:
                with transaction.atomic():
                    WishlistCollection.objects.filter(user=request.user, is_default=True).update(is_default=False)
                    default_collection.is_default = True
                    default_collection.save()
        except WishlistCollection.DoesNotExist:
            # Buat My Wishlist baru jika belum ada
            default_collection = WishlistCollection.objects.create(
                user=request.user,
                name="My Wishlist",
                description="Your default wishlist collection",
                is_default=True
            )
    
    # Refresh collections dan urutkan items berdasarkan created_at
    collections = WishlistCollection.objects.filter(user=request.user).exclude(name="All Wishlist")
    
    # Preload items dengan urutan terbaru
    for collection in collections:
        collection.sorted_items = collection.items.all().select_related('menu_item').order_by('-created_at')
    
    # Hapus All Wishlist jika masih ada
    WishlistCollection.objects.filter(user=request.user, name="All Wishlist").delete()
    
    return render(request, 'collections.html', {
        'collections': collections
    })

@login_required
def collection_add(request):
    if request.method == 'POST':
        form = WishlistCollectionForm(request.POST, user=request.user)
        if form.is_valid():
            collection = form.save(commit=False)
            collection.user = request.user
            collection.save()
            return redirect('wishlist:collection-list')
    else:
        form = WishlistCollectionForm(user=request.user)
    
    return render(request, 'create_collection.html', {
        'form': form,
        'is_add': True
    })

@login_required
def collection_detail(request, collection_id):
    collection = get_object_or_404(WishlistCollection, id=collection_id, user=request.user)
    
    if collection.is_default:
        # Get all items from all collections for this user, ordered by creation date
        items = WishlistItem.objects.filter(
            collection__user=request.user
        ).select_related('menu_item').distinct('menu_item').order_by('-created_at')
    else:
        # For regular collections, order items by creation date
        items = collection.items.all().order_by('-created_at')
        
    return render(request, 'collection_detail.html', {
        'collection': collection,
        'items': items
    })

@login_required
def collection_edit(request, collection_id):
    collection = get_object_or_404(WishlistCollection, id=collection_id, user=request.user)
    
    # Prevent editing default collection
    if collection.is_default:
        return redirect('wishlist:collection-detail', collection_id=collection.id)
    
    if request.method == 'POST':
        form = WishlistCollectionForm(request.POST, instance=collection, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('wishlist:collection-list')  # Diubah dari collection-detail ke collection-list
    else:
        form = WishlistCollectionForm(instance=collection, user=request.user)
    
    return render(request, 'edit_collection.html', {
        'form': form,
        'collection': collection,
        'is_add': False
    })

@login_required
def collection_delete(request, collection_id):
    collection = get_object_or_404(WishlistCollection, id=collection_id, user=request.user)
    
    # Prevent deletion of default collection
    if collection.is_default:
        messages.error(request, 'Cannot delete default collection')
        return redirect('wishlist:collection-detail', collection_id=collection.id)
    
    collection.delete()
    return redirect('wishlist:collection-list')

@login_required
def collection_set_default(request, collection_id):
    collection = get_object_or_404(WishlistCollection, id=collection_id, user=request.user)
    
    if request.method == 'POST':
        with transaction.atomic():
            # Remove default status from other collections
            WishlistCollection.objects.filter(
                user=request.user, 
                is_default=True
            ).update(is_default=False)
            
            # Set this collection as default
            collection.is_default = True
            collection.save()
        
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def get_collections(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        collections = WishlistCollection.objects.filter(user=request.user)
        collections_data = [{
            'id': collection.id,
            'name': collection.name,
            'is_default': collection.is_default
        } for collection in collections]
        return JsonResponse(collections_data, safe=False)
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def item_add(request, menu_item_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        collection_id = data.get('collection_id')
        
        if not collection_id:
            collection = WishlistCollection.objects.filter(
                user=request.user,
                is_default=True
            ).first()
        else:
            collection = get_object_or_404(WishlistCollection, id=collection_id, user=request.user)
            
        menu_item = get_object_or_404(MenuItem, id=menu_item_id)
        
        # Check if item already exists in collection
        if WishlistItem.objects.filter(collection=collection, menu_item=menu_item).exists():
            return JsonResponse({'status': 'exists'})
            
        WishlistItem.objects.create(collection=collection, menu_item=menu_item)
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def item_move(request, item_id, collection_id):
    if request.method == 'POST':
        item = get_object_or_404(WishlistItem, id=item_id, collection__user=request.user)
        new_collection = get_object_or_404(WishlistCollection, id=collection_id, user=request.user)
        
        # Don't allow moving to/from default collection
        if new_collection.is_default:
            return JsonResponse({
                'status': 'error',
                'message': 'Cannot move items to default collection'
            }, status=400)
        
        if item.collection.is_default:
            return JsonResponse({
                'status': 'error',
                'message': 'Cannot move items from default collection'
            }, status=400)
        
        # Check if item already exists in target collection
        if not WishlistItem.objects.filter(
            collection=new_collection, 
            menu_item=item.menu_item
        ).exists():
            item.collection = new_collection
            item.save()
            return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'exists'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def item_remove(request, item_id):
    item = get_object_or_404(WishlistItem, id=item_id, collection__user=request.user)
    collection_id = item.collection.id  # simpan id collection sebelum item dihapus
    
    # When removing from default collection, remove from all collections
    if item.collection.is_default:
        WishlistItem.objects.filter(
            collection__user=request.user,
            menu_item=item.menu_item
        ).delete()
    else:
        item.delete()
        
    return redirect('wishlist:collection-detail', collection_id=collection_id)

@login_required
def add_to_wishlist_from_menu(request):
    menu_item_id = request.GET.get('menu_item')
    if not menu_item_id:
        return JsonResponse({'error': 'No menu item ID provided.'}, status=400)
        
    # Get default collection
    default_collection = WishlistCollection.objects.filter(
        user=request.user,
        name="My Wishlist"
    ).first()
    
    if not default_collection:
        default_collection = WishlistCollection.objects.create(
            user=request.user,
            name="My Wishlist",
            description="Your default wishlist collection",
            is_default=True
        )
    
    menu_item = get_object_or_404(MenuItem, id=menu_item_id)
    
    # Add to default collection
    wishlist_item, created = WishlistItem.objects.get_or_create(
        collection=default_collection,
        menu_item=menu_item
    )
    
    if created:
        response = {'message': 'Item added to wishlist!'}
    else:
        response = {'message': 'Item is already in your wishlist.'}

    # Check if it's an AJAX request
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse(response)
    
    return redirect('product:menu_catalog')

# views untuk fitur Add to
@login_required
def add_item_to_collection(request, item_id, collection_id):
    if request.method == 'POST':
        # Get the item and target collection
        item = get_object_or_404(WishlistItem, id=item_id, collection__user=request.user)
        target_collection = get_object_or_404(WishlistCollection, id=collection_id, user=request.user)
        
        # Don't allow adding to default collection
        if target_collection.is_default:
            return JsonResponse({
                'status': 'error',
                'message': 'Cannot add items to default collection'
            }, status=400)
            
        # Check if item already exists in target collection
        existing_item = WishlistItem.objects.filter(
            collection=target_collection,
            menu_item=item.menu_item
        ).first()
        
        if existing_item:
            return JsonResponse({
                'status': 'error',
                'message': 'Item already exists in this collection'
            }, status=400)
            
        # Create new item in target collection
        WishlistItem.objects.create(
            collection=target_collection,
            menu_item=item.menu_item
        )
        
        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

@login_required
def create_collection_ajax(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name')
            description = data.get('description', '')
            
            if not name:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Collection name is required'
                }, status=400)
                
            if WishlistCollection.objects.filter(user=request.user, name=name).exists():
                return JsonResponse({
                    'status': 'error',
                    'message': 'You already have a collection with this name'
                }, status=400)
            
            collection = WishlistCollection.objects.create(
                user=request.user,
                name=name,
                description=description,
                is_default=False
            )
            
            return JsonResponse({
                'status': 'success',
                'id': collection.id,
                'name': collection.name
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON data'
            }, status=400)
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

@login_required(login_url="authentication:login")
@csrf_exempt
@require_POST
def new_collection_ajax(request):
    name = strip_tags(request.POST.get("name"))
    description = strip_tags(request.POST.get("description", ""))
    user = request.user
    
    errors = {}
    if not name:
        errors['name'] = ["Collection name cannot be empty."]
    if WishlistCollection.objects.filter(user=user, name=name).exists():
        errors['name'] = ["A collection with this name already exists."]
        
    if errors:
        return JsonResponse({"errors": errors}, status=400)
        
    new_collection = WishlistCollection(
        name=name,
        description=description,
        user=user,
        is_default=False
    )
    new_collection.save()
    
    return JsonResponse({
        "message": "Collection created successfully",
        "collection_id": new_collection.id,
        "collection_name": new_collection.name,
    }, status=201)