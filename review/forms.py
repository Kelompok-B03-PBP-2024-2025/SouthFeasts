from django import forms
from .models import ReviewEntry

class ReviewForm(forms.ModelForm):
    class Meta:
        model = ReviewEntry
        fields = ['rating', 'review_text', 'review_image']  # Includes 'review_image' field
        widgets = {
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5, 'step': 0.1}),  # Allow decimal input
            'review_text': forms.Textarea(attrs={'rows': 4, 'cols': 40}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['review_image'].required = True  # Make the image field required

    # Additional validation for the image field
    def clean_review_image(self):
        image = self.cleaned_data.get('review_image')
        if image:
            if image.size > 5 * 1024 * 1024:  # Limit file size to 5 MB
                raise forms.ValidationError("Image file too large (max 5 MB).")
        return image

    # Validation to ensure rating is between 1.0 and 5.0
    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if rating is not None and (rating < 1.0 or rating > 5.0):
            raise forms.ValidationError("Rating must be between 1.0 and 5.0.")
        return rating
