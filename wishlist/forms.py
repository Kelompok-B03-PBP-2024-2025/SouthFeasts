from django import forms
from .models import WishlistCollection

class WishlistCollectionForm(forms.ModelForm):
    class Meta:
        model = WishlistCollection
        fields = ['name', 'description', 'is_default']
        widgets = {
            'name': forms.TextInput(
                attrs={
                    'class': 'w-full p-2 border rounded focus:outline-none focus:border-black',
                    'placeholder': 'Collection Name'
                }
            ),
            'description': forms.Textarea(
                attrs={
                    'class': 'w-full p-2 border rounded focus:outline-none focus:border-black',
                    'placeholder': 'Collection Description (Optional)',
                    'rows': 3
                }
            ),
            'is_default': forms.CheckboxInput(
                attrs={
                    'class': 'h-4 w-4 text-black border-gray-300 rounded focus:ring-black'
                }
            )
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['is_default'].label = "Set as default collection"

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if self.user:
            # Check if collection name exists for this user
            exists = WishlistCollection.objects.filter(
                user=self.user,
                name=name
            ).exists()
            
            # If we're editing, exclude the current instance
            if self.instance.pk:
                exists = exists and self.instance.name != name
                
            if exists:
                raise forms.ValidationError("You already have a collection with this name.")
        return name