from django.shortcuts import render, get_object_or_404, redirect
from product.models import MenuItem
from review.models import ReviewEntry
from django.contrib.auth.decorators import login_required
from review.forms import ReviewForm

# View for displaying all reviews across products
def all_reviews(request):
    reviews = ReviewEntry.objects.all().select_related('menu_item', 'user')
    context = {
        'reviews': reviews,
    }
    return render(request, "all_reviews.html", context)

@login_required(login_url='/auth/login/') 
def create_review(request, item_id):
    """View to handle creating a review for a menu item."""
    menu_item = get_object_or_404(MenuItem, pk=item_id)
    form = ReviewForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        review = form.save(commit=False)
        review.user = request.user  # Assign the current logged-in user to the review
        review.menu_item = menu_item  # Link the review to the menu item
        review.save()
        return redirect('product:menu_detail', id=menu_item.id)

    return render(request, 'create_review.html', {'form': form, 'menu_item': menu_item})

