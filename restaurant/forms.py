from django import forms
from .models import Reservation
from datetime import datetime

class ReservationForm(forms.ModelForm):
    reservation_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text='Select date for your reservation'
    )
    reservation_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time'}),
        help_text='Select time for your reservation'
    )
    number_of_people = forms.IntegerField(
        min_value=1,
        max_value=20,
        initial=1,
        help_text='Number of people for reservation'
    )

    class Meta:
        model = Reservation
        fields = ['restaurant', 'reservation_date', 'reservation_time', 'number_of_people']
    
    def clean(self):
        cleaned_data = super().clean()
        reservation_date = cleaned_data.get('reservation_date')
        reservation_time = cleaned_data.get('reservation_time')
        
        if reservation_date and reservation_time:
            reservation_datetime = datetime.combine(reservation_date, reservation_time)
            if reservation_datetime < datetime.now():
                raise forms.ValidationError("Reservation date and time cannot be in the past!")
        
        return cleaned_data
