from django import forms
from product.models import MenuItem
from restaurant.models import Restaurant
from django.utils.html import strip_tags

# Form untuk MenuItem
class MenuItemForm(forms.ModelForm):
    # Field dari model Restaurant
    resto_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
            'placeholder': 'Nama restoran'
        })
    )
    kecamatan = forms.ChoiceField(
        choices=Restaurant.KECAMATAN_CHOICE,
        widget=forms.Select(attrs={
            'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
        })
    )
    location = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
            'rows': 2,
            'placeholder': 'Alamat lengkap'
        })
    )

    class Meta:
        model = MenuItem
        fields = ['name', 'image', 'description', 'category', 'price', 'resto_name', 'kecamatan', 'location']
        
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
                'placeholder': 'Nama makanan'
            }),
            'image': forms.URLInput(attrs={
                'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
                'rows': 4,
                'placeholder': 'Deskripsi makanan'
            }),
            'category': forms.Select(
                choices=MenuItem.CATEGORY_CHOICES,
                attrs={
                    'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm'
                }
            ),
            'price': forms.NumberInput(attrs={
                'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
                'placeholder': 'Harga'
            })
        }

    # Override method save untuk menyimpan data
    def save(self, commit=True):
        # Dapatkan atau buat restoran terlebih dahulu
        restaurant, created = Restaurant.objects.get_or_create(
            name=self.cleaned_data['resto_name'],
            defaults={
                'kecamatan': self.cleaned_data['kecamatan'],
                'location': self.cleaned_data['location'],
                'city': 'Jakarta Selatan'  # Kota default
            }
        )
        
        # Jika restoran sudah ada tetapi detailnya berubah, perbarui
        if not created:
            restaurant.kecamatan = self.cleaned_data['kecamatan']
            restaurant.location = self.cleaned_data['location']
            restaurant.save()

        # Simpan menu item
        menu_item = super().save(commit=False)
        menu_item.restaurant = restaurant
        
        if commit:
            menu_item.save()
        
        return menu_item

    # Override method __init__ untuk inisialisasi form
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Jika sedang mengedit item yang sudah ada, isi field restoran
            self.fields['resto_name'].initial = self.instance.restaurant.name
            self.fields['kecamatan'].initial = self.instance.restaurant.kecamatan
            self.fields['location'].initial = self.instance.restaurant.location
    
    # Method untuk membersihkan field name
    def clean_name(self):
        return strip_tags(self.cleaned_data["name"])

    # Method untuk membersihkan field description
    def clean_description(self):
        return strip_tags(self.cleaned_data["description"])

    # Method untuk membersihkan field image
    def clean_image(self):
        return strip_tags(self.cleaned_data["image"])

    # Method untuk membersihkan field resto_name
    def clean_resto_name(self):
        return strip_tags(self.cleaned_data["resto_name"])

    # Method untuk membersihkan field location
    def clean_location(self):
        return strip_tags(self.cleaned_data["location"])

# Form untuk Restaurant
class RestaurantForm(forms.ModelForm):
    class Meta:
        model = Restaurant
        fields = ['name', 'location', 'kecamatan']
        labels = {
            'name': 'Nama Restaurant',
            'location': 'Alamat',
            'kecamatan': 'Kecamatan'
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
                'placeholder': 'Masukkan nama restaurant'
            }),
            'location': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
                'rows': 2,
                'placeholder': 'Masukkan alamat lengkap'
            }),
            'kecamatan': forms.Select(
                choices=Restaurant.KECAMATAN_CHOICE,
                attrs={
                    'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm'
                }
            )
        }