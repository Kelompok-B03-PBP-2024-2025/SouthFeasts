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
from django.shortcuts import render, get_object_or_404
from product.models import MenuItem
from review.models import ReviewEntry
from review.forms import ReviewForm
from wishlist.models import WishlistItem 

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
    }
    
    return render(request, 'menu_catalog.html', context)

# def menu_detail(request, item_id):
#     """View untuk menampilkan detail menu item"""
#     menu_item = get_object_or_404(MenuItem, pk=item_id)

#     context = {
#         'menu_item': menu_item,
#         'restaurant': menu_item.restaurant,
#     }
    
#     return render(request, 'menu_detail.html', context)

def menu_detail(request, id):
    """View untuk menampilkan detail menu item"""
    menu_item = get_object_or_404(MenuItem, pk=id)
    reviews = ReviewEntry.objects.filter(menu_item=menu_item).select_related('user')
    form = ReviewForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        review = form.save(commit=False)
        review.user = request.user
        review.product = menu_item
        review.save()
        return redirect('product:menu_detail', id=menu_item.id)

    context = {
        'menu_item': menu_item,
        'restaurant': menu_item.restaurant,
        'reviews' : reviews,
        'form': form,
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


# from django.views.generic import ListView, DetailView
# from django.db.models import Q, Avg
# from .models import Restaurant, MenuItem
# from django.shortcuts import render
# from django.core.paginator import Paginator

# class RestaurantListView(ListView):
#     model = Restaurant
#     template_name = 'product/restaurant_list.html'
#     context_object_name = 'restaurants'
#     paginate_by = 12

#     def get_queryset(self):
#         queryset = Restaurant.objects.all()
#         search_query = self.request.GET.get('search', '')
#         kecamatan = self.request.GET.get('kecamatan', '')
        
#         if search_query:
#             queryset = queryset.filter(
#                 Q(name__icontains=search_query) |
#                 Q(location__icontains=search_query)
#             )
        
#         if kecamatan:
#             queryset = queryset.filter(kecamatan=kecamatan)
            
#         return queryset

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['kecamatans'] = Restaurant.objects.values_list('kecamatan', flat=True).distinct()
#         context['search_query'] = self.request.GET.get('search', '')
#         context['selected_kecamatan'] = self.request.GET.get('kecamatan', '')
#         return context

# class RestaurantDetailView(DetailView):
#     model = Restaurant
#     template_name = 'product/restaurant_detail.html'
#     context_object_name = 'restaurant'

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         # Get menu items for this restaurant
#         context['menu_items'] = self.object.menu_items.all()
#         return context

# class MenuCatalogView(ListView):
#     model = MenuItem
#     template_name = 'product/menu_catalog.html'
#     context_object_name = 'menu_items'
#     paginate_by = 12

#     def get_queryset(self):
#         queryset = MenuItem.objects.all().select_related('restaurant')
        
#         # Apply filters
#         category = self.request.GET.get('category')
#         min_price = self.request.GET.get('min_price')
#         max_price = self.request.GET.get('max_price')
#         kecamatan = self.request.GET.get('kecamatan')
#         search_query = self.request.GET.get('search')
        
#         if category:
#             queryset = queryset.filter(category=category)
        
#         if min_price:
#             queryset = queryset.filter(price__gte=min_price)
        
#         if max_price:
#             queryset = queryset.filter(price__lte=max_price)
        
#         if kecamatan:
#             queryset = queryset.filter(restaurant__kecamatan=kecamatan)
            
#         if search_query:
#             queryset = queryset.filter(
#                 Q(name__icontains=search_query) |
#                 Q(description__icontains=search_query) |
#                 Q(restaurant__name__icontains=search_query)
#             )
            
#         # Sort options
#         sort = self.request.GET.get('sort')
#         if sort == 'price_low':
#             queryset = queryset.order_by('price')
#         elif sort == 'price_high':
#             queryset = queryset.order_by('-price')
#         elif sort == 'name':
#             queryset = queryset.order_by('name')
            
#         return queryset

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['categories'] = MenuItem.CATEGORY_CHOICES
#         context['kecamatans'] = Restaurant.objects.values_list('kecamatan', flat=True).distinct()
        
#         # Add filter values to context
#         context['selected_category'] = self.request.GET.get('category', '')
#         context['selected_kecamatan'] = self.request.GET.get('kecamatan', '')
#         context['min_price'] = self.request.GET.get('min_price', '')
#         context['max_price'] = self.request.GET.get('max_price', '')
#         context['search_query'] = self.request.GET.get('search', '')
#         context['selected_sort'] = self.request.GET.get('sort', '')
        
#         return context