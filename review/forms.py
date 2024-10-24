from django import forms
from .models import ReviewEntry

class ReviewForm(forms.ModelForm):
    class Meta:
        model = ReviewEntry
        fields = ['rating', 'review_text', 'review_image']  # Added 'image' field
        widgets = {
            'rating': forms.RadioSelect(choices=[(i, f'{i} Stars') for i in range(1, 6)]),
            'review_text': forms.Textarea(attrs={'rows': 4, 'cols': 40}),
        }
    
    # Additional validation for the image field (optional)
    def clean_image(self):
        image = self.cleaned_data.get('review_image')
        if image:
            if image.size > 5 * 1024 * 1024:  # Limit file size to 5 MB
                raise forms.ValidationError("Image file too large (max 5 MB).")
        return image
