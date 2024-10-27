from django.shortcuts import render
from forum.models import Article  # Import the Article model from the forum app
from review.models import ReviewEntry
from product.models import MenuItem  # Import the MenuItem model

def show_main(request):
    articles = Article.objects.all().order_by('-created_at')[:3]  # Fetch 3 latest articles
    reviews = ReviewEntry.objects.all().order_by('-created_at')[:4]  # Fetch 4 latest reviews
    products = MenuItem.objects.order_by('?')[:8]  # Fetch 8 random products

    context = {
        "user": request.user,
        "articles": articles,  # Pass articles to the template
        "reviews": reviews,  # Pass reviews to the template
        "products": products,  # Pass random products to the template
    }
    return render(request, "main.html", context)