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
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@login_required(login_url='authentication:login')
def collection_list(request):
    collections = WishlistCollection.objects.filter(user=request.user).exclude(name="All Wishlist")
    
    default_collection = collections.filter(is_default=True).first()
    if not default_collection:
        try:
            default_collection = WishlistCollection.objects.get(
                user=request.user,
                name="My Wishlist"
            )
            if not default_collection.is_default:
                with transaction.atomic():
                    WishlistCollection.objects.filter(user=request.user, is_default=True).update(is_default=False)
                    default_collection.is_default = True
                    default_collection.save()
        except WishlistCollection.DoesNotExist:
            default_collection = WishlistCollection.objects.create(
                user=request.user,
                name="My Wishlist",
                description="Your default wishlist collection",
                is_default=True
            )
    
    collections = WishlistCollection.objects.filter(user=request.user).exclude(name="All Wishlist")
    
    for collection in collections:
        collection.sorted_items = collection.items.all().select_related('menu_item').order_by('-created_at')
    
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
        items = WishlistItem.objects.filter(
            collection__user=request.user
        ).select_related('menu_item').distinct('menu_item').order_by('-created_at')
    else:
        items = collection.items.all().order_by('-created_at')
        
    return render(request, 'collection_detail.html', {
        'collection': collection,
        'items': items
    })

@login_required
def collection_edit(request, collection_id):
    collection = get_object_or_404(WishlistCollection, id=collection_id, user=request.user)
    
    if collection.is_default:
        return redirect('wishlist:collection-detail', collection_id=collection.id)
    
    if request.method == 'POST':
        form = WishlistCollectionForm(request.POST, instance=collection, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('wishlist:collection-list')  
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
            WishlistCollection.objects.filter(
                user=request.user, 
                is_default=True
            ).update(is_default=False)
            
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

@login_required(login_url='authentication:login')
def item_add(request, menu_item_id):
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return JsonResponse({
                'error': 'Authentication required',
                'login_url': reverse('authentication:login')
            }, status=401)

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
    collection_id = item.collection.id  
    
    if item.collection.is_default:
        WishlistItem.objects.filter(
            collection__user=request.user,
            menu_item=item.menu_item
        ).delete()
    else:
        item.delete()
        
    return redirect('wishlist:collection-detail', collection_id=collection_id)

@login_required(login_url='authentication:login')
def add_to_wishlist_from_menu(request):
    if not request.user.is_authenticated:
        return redirect('authentication:login')

    menu_item_id = request.GET.get('menu_item')
    if not menu_item_id:
        messages.error(request, 'No menu item ID provided.')
        return redirect(request.META.get('HTTP_REFERER', 'product:menu_catalog'))
        
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
    
    existing_item = WishlistItem.objects.filter(
        collection__user=request.user,
        menu_item=menu_item
    ).first()
    
    if existing_item:
        WishlistItem.objects.filter(
            collection__user=request.user,
            menu_item=menu_item
        ).delete()
       
    else:
        WishlistItem.objects.create(
            collection=default_collection,
            menu_item=menu_item
        )

    return redirect(request.META.get('HTTP_REFERER', 'product:menu_catalog'))

@login_required
def add_item_to_collection(request, item_id, collection_id):
    if request.method == 'POST':
        item = get_object_or_404(WishlistItem, id=item_id, collection__user=request.user)
        target_collection = get_object_or_404(WishlistCollection, id=collection_id, user=request.user)
        
        if target_collection.is_default:
            return JsonResponse({
                'status': 'error',
                'message': 'Cannot add items to default collection'
            }, status=400)
            
        existing_item = WishlistItem.objects.filter(
            collection=target_collection,
            menu_item=item.menu_item
        ).first()
        
        if existing_item:
            return JsonResponse({
                'status': 'error',
                'message': 'Item already exists in this collection'
            }, status=400)
            
        WishlistItem.objects.create(
            collection=target_collection,
            menu_item=item.menu_item
        )
        
        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


# @login_required(login_url='authentication:login')
# def create_collection_ajax(request):
#     if not request.user.is_authenticated:
#         return JsonResponse({
#             'error': 'Authentication required',
#             'login_url': reverse('authentication:login')
#         }, status=401)

#     if request.method == 'POST':
#         name = request.POST.get('name', '').strip()
#         description = request.POST.get('description', '').strip()
        
#         errors = {}
        
#         if not name:
#             errors['name'] = ["Collection name cannot be empty."]
#         elif WishlistCollection.objects.filter(user=request.user, name=name).exists():
#             errors['name'] = ["A collection with this name already exists."]
            
#         if errors:
#             return JsonResponse({"errors": errors}, status=400)
            
#         try:
#             collection = WishlistCollection.objects.create(
#                 user=request.user,
#                 name=name,
#                 description=description,
#                 is_default=False
#             )
            
#             return JsonResponse({
#                 "message": "Collection created successfully",
#                 "collection_id": collection.id,
#                 "collection_name": collection.name
#             }, status=201)
            
#         except Exception as e:
#             return JsonResponse({
#                 "errors": {"server": [str(e)]}
#             }, status=500)
            
#     return JsonResponse({"errors": {"method": ["Invalid request method"]}}, status=405)
@login_required(login_url='authentication:login')
@csrf_exempt  # Tambahkan ini
def create_collection_ajax(request):
    if not request.user.is_authenticated:
        return JsonResponse({
            'error': 'Authentication required',
            'login_url': reverse('authentication:login')
        }, status=401)

    if request.method == 'POST':
        try:
            # Untuk handle request dari Flutter
            if request.body:
                data = json.loads(request.body)
                name = data.get('name', '').strip()
                description = data.get('description', '').strip()
            # Untuk handle request dari web
            else:
                name = request.POST.get('name', '').strip()
                description = request.POST.get('description', '').strip()
            
            errors = {}
            
            if not name:
                errors['name'] = ["Collection name cannot be empty."]
            elif WishlistCollection.objects.filter(user=request.user, name=name).exists():
                errors['name'] = ["A collection with this name already exists."]
                
            if errors:
                return JsonResponse({"errors": errors}, status=400)
                
            collection = WishlistCollection.objects.create(
                user=request.user,
                name=name,
                description=description,
                is_default=False
            )
            
            # Return format sesuai model WishlistCollection Flutter
            return JsonResponse({
                'results': [{
                    'id': collection.id,
                    'name': collection.name,
                    'description': collection.description,
                    'is_default': collection.is_default,
                    'items': [],
                    'items_count': 0
                }],
                'total_pages': 1,
                'current_page': 1,
                'has_previous': False,
                'has_next': False,
                'total_items': 1,
                'filter_type': 'all',
                'search_query': ''
            }, status=201)
                
        except Exception as e:
            return JsonResponse({
                "errors": {"server": [str(e)]}
            }, status=500)
            
    return JsonResponse({"errors": {"method": ["Invalid request method"]}}, status=405)

@login_required(login_url='authentication:login')
@csrf_exempt
@require_POST
def new_collection_ajax(request):
    if not request.user.is_authenticated:
        return JsonResponse({
            'error': 'Authentication required',
            'login_url': reverse('authentication:login')
        }, status=401)

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

# **FLUTTER**
@login_required
def show_json(request):
    """API endpoint untuk data wishlist collections"""
    try:
        # Get filter parameters
        collection_type = request.GET.get('type', 'all')  # Filter by collection type (all/default/custom)
        search_query = request.GET.get('search', '').strip()
        page = int(request.GET.get('page', 1))
        per_page = 6  # Items per page

        # Base queryset
        collections = WishlistCollection.objects.filter(
            user=request.user
        ).exclude(name="All Wishlist")

        # Apply filters
        if search_query:
            collections = collections.filter(name__icontains=search_query)
            
        if collection_type == 'default':
            collections = collections.filter(is_default=True)
        elif collection_type == 'custom':
            collections = collections.filter(is_default=False)

        # Pagination
        total_items = collections.count()
        total_pages = (total_items + per_page - 1) // per_page
        start = (page - 1) * per_page
        end = start + per_page
        
        collections = collections[start:end]

        # Format response data
        results = []
        for collection in collections:
            # Get items for each collection
            items = collection.items.all().select_related('menu_item')
            
            items_data = [{
                'id': item.id,
                'menu_item': {
                    'id': item.menu_item.id,
                    'name': item.menu_item.name,
                    'price': str(item.menu_item.price)
                },
                'created_at': item.created_at.strftime('%d %b, %Y')
            } for item in items]

            # Collection data
            collection_data = {
                'id': collection.id,
                'name': collection.name,
                'description': collection.description or "",
                'is_default': collection.is_default,
                'items': items_data,
                'items_count': len(items_data)
            }
            results.append(collection_data)

        # Return formatted response
        return JsonResponse({
            'results': results,
            'total_pages': total_pages,
            'current_page': page,
            'has_previous': page > 1,
            'has_next': page < total_pages,
            'total_items': total_items,
            'filter_type': collection_type,
            'search_query': search_query
        })

    except Exception as e:
        return JsonResponse({
            'status': False,
            'message': str(e)
        }, status=500)

@login_required
def get_collections_flutter(request):
    """Mendapatkan semua koleksi user untuk Flutter"""
    collections = WishlistCollection.objects.filter(
        user=request.user
    ).exclude(name="All Wishlist")
    
    data = []
    for collection in collections:
        items_data = []
        for item in collection.items.all().select_related('menu_item'):
            items_data.append({
                'id': item.id,
                'menu_item': {
                    'id': item.menu_item.id,
                    'name': item.menu_item.name,
                    'price': str(item.menu_item.price),
                    'image': str(item.menu_item.image.url) if item.menu_item.image else None,
                },
                'created_at': item.created_at.isoformat()
            })
            
        data.append({
            'id': collection.id,
            'name': collection.name,
            'description': collection.description,
            'is_default': collection.is_default,
            'items': items_data
        })
    
    return JsonResponse(data, safe=False)

@csrf_exempt
@login_required
def create_collection_flutter(request):
    """Membuat koleksi baru dari Flutter"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        
        if not name:
            return JsonResponse({'error': 'Collection name is required'}, status=400)
            
        if WishlistCollection.objects.filter(user=request.user, name=name).exists():
            return JsonResponse({'error': 'Collection name already exists'}, status=400)
            
        collection = WishlistCollection.objects.create(
            user=request.user,
            name=name,
            description=description,
            is_default=False
        )
        
        return JsonResponse({
            'id': collection.id,
            'name': collection.name,
            'description': collection.description,
            'is_default': collection.is_default,
            'items': []
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
@login_required(login_url='authentication:login')
@csrf_exempt
@require_POST
def create_collection_flutter(request):
    """Membuat koleksi baru dari Flutter"""
    if not request.user.is_authenticated:
        return JsonResponse({
            'error': 'Authentication required',
            'login_url': reverse('authentication:login')
        }, status=401)
        
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        
        if not name:
            return JsonResponse({'error': 'Collection name is required'}, status=400)
            
        if WishlistCollection.objects.filter(user=request.user, name=name).exists():
            return JsonResponse({'error': 'Collection with this name already exists'}, status=400)
            
        collection = WishlistCollection.objects.create(
            user=request.user,
            name=name,
            description=description,
            is_default=False
        )
        
        # Return format sesuai dengan yang diharapkan Flutter
        return JsonResponse({
            'id': collection.id,
            'name': collection.name,
            'description': collection.description,
            'is_default': collection.is_default,
            'items': []
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@login_required
def delete_collection_flutter(request, collection_id):
    """Menghapus koleksi dari Flutter"""
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    collection = get_object_or_404(WishlistCollection, id=collection_id, user=request.user)
    
    if collection.is_default:
        return JsonResponse({'error': 'Cannot delete default collection'}, status=400)
        
    collection.delete()
    return JsonResponse({'message': 'Collection deleted successfully'})

@csrf_exempt
@login_required
def add_to_wishlist_flutter(request):
    """Menambahkan item ke wishlist dari Flutter"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    try:
        data = json.loads(request.body)
        menu_item_id = data.get('menu_item_id')
        collection_id = data.get('collection_id')
        
        if not menu_item_id:
            return JsonResponse({'error': 'Menu item ID is required'}, status=400)
            
        menu_item = get_object_or_404(MenuItem, id=menu_item_id)
        
        if not collection_id:
            collection = WishlistCollection.objects.filter(
                user=request.user,
                is_default=True
            ).first()
            
            if not collection:
                collection = WishlistCollection.objects.create(
                    user=request.user,
                    name="My Wishlist",
                    description="Your default wishlist collection",
                    is_default=True
                )
        else:
            collection = get_object_or_404(
                WishlistCollection, 
                id=collection_id,
                user=request.user
            )
            
        if WishlistItem.objects.filter(collection=collection, menu_item=menu_item).exists():
            return JsonResponse({'error': 'Item already in collection'}, status=400)
            
        item = WishlistItem.objects.create(
            collection=collection,
            menu_item=menu_item
        )
        
        return JsonResponse({
            'id': item.id,
            'menu_item': {
                'id': menu_item.id,
                'name': menu_item.name,
                'price': str(menu_item.price),
                'image': str(menu_item.image.url) if menu_item.image else None,
            },
            'created_at': item.created_at.isoformat()
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

@csrf_exempt
@login_required
def remove_from_wishlist_flutter(request, item_id):
    """Menghapus item dari wishlist dari Flutter"""
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    item = get_object_or_404(WishlistItem, id=item_id, collection__user=request.user)
    
    if item.collection.is_default:
        WishlistItem.objects.filter(
            collection__user=request.user,
            menu_item=item.menu_item
        ).delete()
    else:
        item.delete()
        
    return JsonResponse({'message': 'Item removed successfully'})

@csrf_exempt
@login_required
def move_item_flutter(request):
    """Memindahkan item antar koleksi dari Flutter"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    try:
        data = json.loads(request.body)
        item_id = data.get('item_id')
        target_collection_id = data.get('target_collection_id')
        
        if not all([item_id, target_collection_id]):
            return JsonResponse({'error': 'Item ID and target collection ID are required'}, status=400)
            
        item = get_object_or_404(WishlistItem, id=item_id, collection__user=request.user)
        target_collection = get_object_or_404(
            WishlistCollection,
            id=target_collection_id,
            user=request.user
        )
        
        if target_collection.is_default:
            return JsonResponse({'error': 'Cannot move items to default collection'}, status=400)
            
        if item.collection.is_default:
            return JsonResponse({'error': 'Cannot move items from default collection'}, status=400)
            
        if WishlistItem.objects.filter(
            collection=target_collection,
            menu_item=item.menu_item
        ).exists():
            return JsonResponse({'error': 'Item already exists in target collection'}, status=400)
            
        item.collection = target_collection
        item.save()
        
        return JsonResponse({'message': 'Item moved successfully'})
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
@login_required
def get_default_collection(request):
    default_collection_name = "All Items"
    default_collection, created = WishlistCollection.objects.get_or_create(
        user=request.user,
        name=default_collection_name,
        defaults={
            'description': 'Default collection containing all items',
            'is_default': True
        }
    )

    all_items = WishlistItem.objects.filter(collection__user=request.user).select_related('menu_item')
    default_collection.items.set(all_items)

    items_data = [{
        'id': item.id,
        'menu_item': {
            'id': item.menu_item.id,
            'name': item.menu_item.name,
            'price': str(item.menu_item.price),
            'image': str(item.menu_item.image.url) if item.menu_item.image else None,
        },
        'created_at': item.created_at.isoformat()
    } for item in all_items]

    data = {
        'id': default_collection.id,
        'name': default_collection.name,
        'description': default_collection.description,
        'is_default': default_collection.is_default,
        'items': items_data
    }

    return JsonResponse(data)