from django.contrib import admin
from .models import Booking, PickupRequest


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('booking_id', 'customer_name', 'product', 'drop_off_date', 'status', 'total_amount')
    list_filter = ('status', 'payment_status', 'drop_off_date', 'created_at')
    search_fields = ('booking_id', 'customer_email', 'customer_name', 'customer_phone')
    readonly_fields = ('booking_id', 'created_at', 'updated_at', 'confirmed_at')
    
    fieldsets = (
        ('Booking ID', {
            'fields': ('booking_id',)
        }),
        ('Customer Information', {
            'fields': ('customer_name', 'customer_email', 'customer_phone')
        }),
        ('Product & Duration', {
            'fields': ('product', 'drop_off_date', 'pickup_date', 'rental_months')
        }),
        ('Delivery Address', {
            'fields': ('delivery_address', 'delivery_city', 'delivery_state', 'delivery_zip', 'delivery_notes')
        }),
        ('Pricing', {
            'fields': ('monthly_rate', 'delivery_fee', 'pickup_fee', 'total_amount')
        }),
        ('Payment & Status', {
            'fields': ('payment_status', 'status', 'stripe_payment_intent_id', 'stripe_charge_id')
        }),
        ('Notifications', {
            'fields': ('confirmation_email_sent', 'confirmation_sms_sent', 'drop_off_reminder_sent', 'pickup_reminder_sent'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'confirmed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PickupRequest)
class PickupRequestAdmin(admin.ModelAdmin):
    list_display = ('booking', 'requested_pickup_date', 'payment_status', 'created_at')
    list_filter = ('payment_status', 'requested_pickup_date', 'created_at')
    search_fields = ('booking__booking_id', 'booking__customer_email')
    readonly_fields = ('created_at', 'confirmed_at')
    
    fieldsets = (
        ('Booking Reference', {
            'fields': ('booking',)
        }),
        ('Pickup Details', {
            'fields': ('requested_pickup_date', 'pickup_address', 'pickup_notes')
        }),
        ('Payment', {
            'fields': ('payment_status', 'stripe_payment_intent_id')
        }),
        ('Notifications', {
            'fields': ('pickup_email_sent', 'pickup_sms_sent'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'confirmed_at'),
            'classes': ('collapse',)
        }),
    )
