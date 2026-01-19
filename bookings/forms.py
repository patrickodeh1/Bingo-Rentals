from django import forms
from .models import Booking

# Country codes - Canada/United States only
COUNTRY_CODES = [
    ('+1', '+1 (Canada/United States)'),
]

# Distance range choices
DISTANCE_RANGE_CHOICES = [
    ('0-30', 'Within 30 km ($250)'),
    ('30-100', '30 to 100 km ($375)'),
    ('100+', 'Beyond 100 km (Contact for quote)'),
]


class BookingForm(forms.Form):
    """Form for capturing customer details during checkout"""
    customer_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Full Name',
            'required': True
        })
    )
    customer_email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@example.com',
            'required': True
        })
    )
    country_code = forms.ChoiceField(
        choices=COUNTRY_CODES,
        initial='+1',
        widget=forms.Select(attrs={
            'class': 'form-control',
            'required': True
        })
    )
    customer_phone = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '(416) 555-0123',
            'required': True
        })
    )
    delivery_address = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': '100 King Street West, Suite 200',
            'required': True
        })
    )
    delivery_city = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Toronto',
            'required': True
        })
    )
    delivery_state = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'ON',
            'required': True
        })
    )
    delivery_zip = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'M5H 2N2',
            'required': True
        })
    )
    delivery_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Any special instructions or access notes'
        })
    )
    
    delivery_distance_range = forms.ChoiceField(
        choices=DISTANCE_RANGE_CHOICES,
        label='Delivery Distance Range',
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input',
            'required': True
        }),
        help_text='Select the distance range that best matches your location'
    )
    
    def clean(self):
        return super().clean()


class PickupRequestForm(forms.Form):
    """Form for scheduling pickup"""
    booking_id = forms.UUIDField(widget=forms.HiddenInput())
    customer_email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email used for booking',
            'required': True
        })
    )
    requested_pickup_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'required': True
        })
    )
    pickup_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Any special instructions for pickup'
        })
    )
