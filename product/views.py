# product/views.py
from django.shortcuts import redirect, render, get_object_or_404
from django.core.paginator import Paginator
from .models import MenuItem
from restaurant.models import Restaurant
from django.db.models import Q
from django.http import JsonResponse
from .models import MenuItem
from restaurant.models import Restaurant
import csv
import pandas as pd
from decimal import Decimal
from product.models import MenuItem
from review.models import ReviewEntry
from review.forms import ReviewForm
from wishlist.models import WishlistItem 
from django.db.models import Avg

def menu_catalog(request):
    """View untuk menampilkan katalog menu dengan fitur filter dan search"""
    # Ambil semua menu items
    menu_items = MenuItem.objects.all().select_related('restaurant')
    
    # Handle search
    search_query = request.GET.get('search', '')
    if search_query:
        menu_items = menu_items.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(restaurant__name__icontains=search_query)
        )
    
    # Handle filter kategori
    category = request.GET.get('category', '')
    if category:
        menu_items = menu_items.filter(category=category)
    
    # Handle filter harga
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        menu_items = menu_items.filter(price__gte=min_price)
    if max_price:
        menu_items = menu_items.filter(price__lte=max_price)
    
    # Handle filter lokasi
    kecamatan = request.GET.get('kecamatan')
    if kecamatan:
        menu_items = menu_items.filter(restaurant__kecamatan=kecamatan)
    
    # Pagination
    paginator = Paginator(menu_items, 12)  # 12 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Data untuk dropdown filter
    categories = MenuItem.CATEGORY_CHOICES
    kecamatans = Restaurant.objects.values_list('kecamatan', flat=True).distinct()

    # Tambahkan pengecekan wishlist untuk setiap item
    if request.user.is_authenticated:
        for item in page_obj:
            item.is_in_wishlist = WishlistItem.objects.filter(
                collection__user=request.user,
                menu_item=item
            ).exists()
    
    context = {
        'menu_items': page_obj,
        'categories': categories,
        'kecamatans': kecamatans,
        'search_query': search_query,
        'selected_category': category,
        'min_price': min_price,
        'max_price': max_price,
        'selected_kecamatan': kecamatan,
        'restaurant_kecamatan_choices': Restaurant.KECAMATAN_CHOICE,
    }
    
    return render(request, 'menu_catalog.html', context)

def menu_detail(request, id):
    """View untuk menampilkan detail menu item"""
    menu_item = get_object_or_404(MenuItem, pk=id)
    reviews = ReviewEntry.objects.filter(menu_item=menu_item).select_related('user')
    form = ReviewForm(request.POST or None)

    # Tambahkan pengecekan wishlist
    if request.user.is_authenticated:
        menu_item.is_in_wishlist = WishlistItem.objects.filter(
            collection__user=request.user,
            menu_item=menu_item
        ).exists()
    else:
        menu_item.is_in_wishlist = False

    # Jika ada review baru yang disubmit
    if request.method == 'POST' and form.is_valid():
        review = form.save(commit=False)
        review.user = request.user
        review.menu_item = menu_item  # Pastikan untuk mengisi field 'menu_item'
        review.save()
        return redirect('product:menu_detail', id=menu_item.id)

    # Menghitung rata-rata rating dari semua review terkait menu_item
    average_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0  # Default ke 0 jika belum ada review
    
    context = {
        'menu_item': menu_item,
        'restaurant': menu_item.restaurant,
        'reviews': reviews,
        'form': form,
        'average_rating': round(average_rating, 1)  # Tambahkan rata-rata rating ke context
    }
    
    return render(request, 'menu_detail.html', context)

def restaurant_menu(request, restaurant_id):
    """View untuk menampilkan semua menu dari restoran tertentu"""
    restaurant = get_object_or_404(Restaurant, pk=restaurant_id)
    menu_items = MenuItem.objects.filter(restaurant=restaurant)
    
    context = {
        'restaurant': restaurant,
        'menu_items': menu_items,
    }
    
    return render(request, 'restaurant_menu.html', context)

def initialize_data(request):
    try:
        # Hapus data yang ada (opsional, comment jika tidak ingin menghapus data)
        # Restaurant.objects.all().delete()
        # MenuItem.objects.all().delete()

        # Baca dataset
        df = pd.read_csv('dataset/dataset_makanan.csv')
        
        # Inisialisasi dictionary untuk tracking restaurant
        restaurants_dict = {}
        
        # Iterasi setiap baris dataset
        for index, row in df.iterrows():
            # Buat atau ambil restaurant
            restaurant_name = row['Resto Name']
            if restaurant_name not in restaurants_dict:
                restaurant = Restaurant.objects.create(
                    name=restaurant_name,
                    city=row['City'],
                    kecamatan=row['Kecamatan'],
                    location=row['Location']
                )
                restaurants_dict[restaurant_name] = restaurant
            else:
                restaurant = restaurants_dict[restaurant_name]
            
            # Buat menu item
            try:
                # Convert price to Decimal, handling any currency symbols or formatting
                price = Decimal(str(row['Price']).replace('Rp', '').replace(',', '').strip())
                
                menu_item = MenuItem.objects.create(
                    name=row['Item'],
                    image=row['Image'],
                    description=row['Description'],
                    category=row['Categories'],
                    price=price,
                    restaurant=restaurant
                )
                print(f"Created menu item: {menu_item.name}")
                
            except Exception as e:
                print(f"Error creating menu item {row['Item']}: {str(e)}")
                continue
        
        return JsonResponse({
            'status': 'success',
            'message': 'Data initialized successfully',
            'restaurants_created': len(restaurants_dict),
            'menu_items_created': MenuItem.objects.count()
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)