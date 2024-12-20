
from django.contrib import messages 
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from product.models import MenuItem
from review.models import ReviewEntry
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from review.forms import ReviewForm
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.http import JsonResponse
from django.db.models import Q
from review.models import ReviewEntry

import json
from django.http import JsonResponse
from django.db.models import Q
from django.views.decorators.http import require_GET
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


# View for displaying all reviews across products with search functionality
def all_reviews(request):
    search_query = request.GET.get('search', '')  # Get search query from URL
    reviews = ReviewEntry.objects.all().select_related('menu_item', 'user')
    
    # Filter reviews based on product name or review content if a search query is provided
    if search_query:
        reviews = reviews.filter(
            Q(menu_item__name__icontains=search_query) |  # Search by product name
            Q(review_text__icontains=search_query)        # Search by review content
        )

    context = {
        'reviews': reviews,
        'search_query': search_query,  # Pass search query to template
    }
    return render(request, "all_reviews.html", context)

# @login_required(login_url='/auth/login/') 
# def create_review(request, item_id):
#     """View to handle creating a review for a menu item."""
#     menu_item = get_object_or_404(MenuItem, pk=item_id)
#     form = ReviewForm(request.POST or None, request.FILES or None)  # Handle image uploads with request.FILES

#     if request.method == 'POST' and form.is_valid():
#         review = form.save(commit=False)
#         review.user = request.user  # Assign the current logged-in user to the review
#         review.menu_item = menu_item  # Link the review to the menu item
#         review.save()
        
#         # Redirect to the menu item detail page after saving
#         return redirect('product:menu_detail', menu_item.id)

#     return render(request, 'create_review.html', {'form': form, 'menu_item': menu_item})
@csrf_exempt
@require_POST
def create_review(request, item_id):
    menu_item = get_object_or_404(MenuItem, pk=item_id)

    review_text = request.POST.get("review_text")
    rating = request.POST.get("rating")
    image_url = request.POST.get("image_url")  # Retrieve image URL from POST data
    user = request.user

    # Create and save the new review entry
    new_review = ReviewEntry(
        menu_item=menu_item,
        review_text=review_text,
        rating=rating,
        image_url=image_url,  # Save image URL in the model
        user=user
    )
    new_review.save()

    # Return JSON response
    return JsonResponse({
        "success": True,
        "user": user.username,
        "review_text": new_review.review_text,
        "rating": new_review.rating,
        "image_url": new_review.image_url  # Return the image URL in the response
    })

def review_detail(request, review_id):
    review = get_object_or_404(ReviewEntry, pk=review_id)
    context = {
        'review': review,
    }
    return render(request, 'review_detail.html', context)
  
@login_required(login_url='/auth/login/')
def edit_review(request, review_id):
    review = get_object_or_404(ReviewEntry, id=review_id)

    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()  # Simpan perubahan pada review
            return redirect('review:all_reviews')  # Redirect ke halaman "All Reviews" setelah penyimpanan
    else:
        form = ReviewForm(instance=review)

    context = {
        'review': review,
        'form': form,
    }
    return render(request, 'edit_review.html', context)

@login_required(login_url='/auth/login/')
def delete_review(request, review_id):
    if request.method == "POST":
        review = get_object_or_404(ReviewEntry, id=review_id)
        if review.user == request.user or request.user.is_staff:
            review.delete()
            messages.success(request, 'Review has been successfully deleted.')
            return redirect('review:all_reviews')
        else:
            return HttpResponseForbidden("You are not allowed to delete this review.")

# def show_json(request):
#     search_query = request.GET.get('search', '')  # Get search query from URL
#     reviews = ReviewEntry.objects.all().select_related('menu_item', 'user')
    
#     # Filter reviews based on product name or review content if a search query is provided
#     if search_query:
#         reviews = reviews.filter(
#             Q(menu_item__name__icontains=search_query) |  # Search by product name
#             Q(review_text__icontains=search_query)        # Search by review content
#         )
    
#     # Create a list of dictionaries with review details
#     reviews_data = [
#         {
#             'id': review.id,
#             'menu_item': review.menu_item.name if review.menu_item else None,
#             'user': review.user.username,
#             'review_text': review.review_text,
#             'rating': review.rating,
#             'review_image': review.review_image.url if review.review_image else None,
#             'created_at': review.created_at.strftime('%Y-%m-%d %H:%M:%S'),
#         }
#         for review in reviews
#     ]
    
#     return JsonResponse(reviews_data, safe=False)  # Set safe=False for returning a list

@csrf_exempt
@require_GET
def show_json(request):
    search_query = request.GET.get('search', '')  # Ambil query pencarian dari parameter GET
    reviews = ReviewEntry.objects.all().select_related('menu_item', 'user')

    # Filter review berdasarkan nama produk atau teks ulasan jika ada query pencarian
    if search_query:
        reviews = reviews.filter(
            Q(menu_item__name__icontains=search_query) |  # Filter berdasarkan nama produk
            Q(review_text__icontains=search_query)        # Filter berdasarkan teks ulasan
        )
    
    # Buat list of dictionaries dengan detail review
    reviews_data = [
        {
            'id': review.id,
            'menu_item': review.menu_item.name if review.menu_item else None,
            'user': review.user.username,
            'review_text': review.review_text,
            'rating': review.rating,
            'image_url': review.image_url,  # Tambahkan image_url
            'created_at': review.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        }
        for review in reviews
    ]
    
    return JsonResponse(reviews_data, safe=False)  # safe=False untuk mengembalikan list

@csrf_exempt
def create_review_flutter(request, item_id):
    if request.method == "POST":
        try:
            # Parse JSON body
            data = json.loads(request.body.decode("utf-8"))
            
            # Validate required fields
            review_text = data.get("review_text")
            rating = data.get("rating")
            user_id = data.get("user_id")
            image_url = data.get("image_url")  # Ambil image_url jika tersedia
            
            if not review_text or not rating or not user_id:
                return JsonResponse({
                    "success": False,
                    "error": "Missing required fields: review_text, rating, or user_id"
                }, status=400)
            
            # Retrieve menu_item and user
            menu_item = MenuItem.objects.get(pk=item_id)
            user = settings.AUTH_USER_MODEL.objects.get(pk=user_id)

            # Create and save the new review entry
            new_review = ReviewEntry(
                menu_item=menu_item,
                review_text=review_text,
                rating=rating,
                user=user,
                image_url=image_url  # Tambahkan image_url ke ReviewEntry
            )
            new_review.save()

            return JsonResponse({
                "success": True,
                "message": "Review created successfully",
                "data": {
                    "id": new_review.id,
                    "menu_item": new_review.menu_item.name,
                    "user": new_review.user.username,
                    "review_text": new_review.review_text,
                    "rating": new_review.rating,
                    "image_url": new_review.image_url,  # Sertakan image_url di respons
                    "created_at": new_review.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                }
            })
        except MenuItem.DoesNotExist:
            return JsonResponse({
                "success": False,
                "error": "Menu item not found"
            }, status=404)
        except settings.AUTH_USER_MODEL.DoesNotExist:
            return JsonResponse({
                "success": False,
                "error": "User not found"
            }, status=404)
        except Exception as e:
            return JsonResponse({
                "success": False,
                "error": str(e)
            }, status=500)
    else:
        return JsonResponse({
            "success": False,
            "error": "Invalid HTTP method. Use POST."
        }, status=405)


