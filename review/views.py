
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
@login_required
@require_POST
def create_review(request, item_id):
    menu_item = get_object_or_404(MenuItem, pk=item_id)

    review_text = request.POST.get("review_text")
    rating = request.POST.get("rating")
    review_image = request.FILES.get("review_image")
    user = request.user

    # Create and save the new review entry
    new_review = ReviewEntry(
        menu_item=menu_item,
        review_text=review_text,
        rating=rating,
        review_image=review_image,
        user=user
    )
    new_review.save()

    # Return JSON response
    return JsonResponse({
        "success": True,
        "user": user.username,
        "review_text": new_review.review_text,
        "rating": new_review.rating,
        "review_image": new_review.review_image.url if new_review.review_image else None
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

def show_json(request):
    search_query = request.GET.get('search', '')  # Get search query from URL
    reviews = ReviewEntry.objects.all().select_related('menu_item', 'user')
    
    # Filter reviews based on product name or review content if a search query is provided
    if search_query:
        reviews = reviews.filter(
            Q(menu_item__name__icontains=search_query) |  # Search by product name
            Q(review_text__icontains=search_query)        # Search by review content
        )
    
    # Create a list of dictionaries with review details
    reviews_data = [
        {
            'id': review.id,
            'menu_item': review.menu_item.name if review.menu_item else None,
            'user': review.user.username,
            'review_text': review.review_text,
            'rating': review.rating,
            'review_image': review.review_image.url if review.review_image else None,
            'created_at': review.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        }
        for review in reviews
    ]
    
    return JsonResponse(reviews_data, safe=False)  # Set safe=False for returning a list