# from django.shortcuts import render

# # Create your views here.
# restaurant/views.py
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import Restaurant
from product.models import MenuItem
from django.db.models import Q

def restaurant_list(request):
    """View untuk menampilkan daftar restoran dengan filter"""
    # Ambil semua restoran
    restaurants = Restaurant.objects.all()

    # Handle search
    search_query = request.GET.get('search', '')
    if search_query:
        restaurants = restaurants.filter(
            Q(name__icontains=search_query) |
            Q(location__icontains=search_query)
        )

    # Filter berdasarkan kecamatan
    kecamatan = request.GET.get('kecamatan', '')
    if kecamatan:
        restaurants = restaurants.filter(kecamatan=kecamatan)

    # Pagination
    paginator = Paginator(restaurants, 12)  # 12 restoran per halaman
    page = request.GET.get('page')
    restaurants = paginator.get_page(page)

    context = {
        'restaurants': restaurants,
        'kecamatans': Restaurant.KECAMATAN_CHOICE,
        'search_query': search_query,
        'selected_kecamatan': kecamatan,
    }
    
    return render(request, 'restaurant_list.html', context)

def restaurant_detail(request, pk):
    """View untuk menampilkan detail restoran dan menu-menunya"""
    restaurant = get_object_or_404(Restaurant, pk=pk)
    
    # Ambil menu items untuk restoran ini
    menu_items = MenuItem.objects.filter(restaurant=restaurant)

    # Filter menu berdasarkan kategori
    category = request.GET.get('category', '')
    if category:
        menu_items = menu_items.filter(category=category)

    # Filter berdasarkan range harga
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        menu_items = menu_items.filter(price__gte=min_price)
    if max_price:
        menu_items = menu_items.filter(price__lte=max_price)

    context = {
        'restaurant': restaurant,
        'menu_items': menu_items,
        'categories': MenuItem.CATEGORY_CHOICES,
        'selected_category': category,
        'min_price': min_price,
        'max_price': max_price,
    }
    
    return render(request, 'restaurant_detail.html', context)