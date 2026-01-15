from django.contrib import admin
from .models import Product, PricingSetting, BlackoutDate

# Admin interface removed - managed through dashboard instead
            'fields': ('date',)
        }),
        ('Details', {
            'fields': ('reason', 'product')
        }),
    )
