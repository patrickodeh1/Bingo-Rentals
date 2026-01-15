from django.db import models
from django.core.validators import MinValueValidator
from products.models import Product, PricingSetting
import uuid


class BookingStatus(models.TextChoices):
    PENDING = 'pending', 'Pending Payment'
    CONFIRMED = 'confirmed', 'Confirmed'
    IN_PROGRESS = 'in_progress', 'In Progress'
    PICKUP_SCHEDULED = 'pickup_scheduled', 'Pickup Scheduled'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'


class Booking(models.Model):
    """Main booking model for guest checkout"""
    # Unique identifier
    booking_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    
    # Product details
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='bookings'
    )
    
    # Customer information (guest checkout - no user account)
    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20)
    
    # Delivery information
    delivery_address = models.TextField(help_text="Full delivery address")
    delivery_city = models.CharField(max_length=100)
    delivery_state = models.CharField(max_length=50)
    delivery_zip = models.CharField(max_length=10)
    delivery_notes = models.TextField(blank=True)
    
    # Booking dates
    drop_off_date = models.DateField()
    pickup_date = models.DateField(null=True, blank=True)
    rental_months = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )
    
    # Pricing
    monthly_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Rate at time of booking"
    )
    transport_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=80.00,
        help_text="Transport/delivery+removal fee at time of booking"
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    
    # Payment information
    stripe_payment_intent_id = models.CharField(max_length=200, blank=True)
    stripe_charge_id = models.CharField(max_length=200, blank=True)
    payment_status = models.CharField(
        max_length=20,
        default='pending',
        choices=[
            ('pending', 'Pending'),
            ('paid', 'Paid'),
            ('refunded', 'Refunded'),
            ('failed', 'Failed'),
        ]
    )
    
    # Booking status
    status = models.CharField(
        max_length=20,
        choices=BookingStatus.choices,
        default=BookingStatus.PENDING
    )
    
    # Notifications
    confirmation_email_sent = models.BooleanField(default=False)
    confirmation_sms_sent = models.BooleanField(default=False)
    drop_off_reminder_sent = models.BooleanField(default=False)
    pickup_reminder_sent = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'drop_off_date']),
            models.Index(fields=['customer_email']),
        ]
    
    def __str__(self):
        return f"{self.booking_id} - {self.customer_name} - {self.product.name}"
    
    def calculate_total(self):
        """Calculate total booking amount"""
        monthly_cost = self.monthly_rate * self.rental_months
        total = monthly_cost + self.delivery_fee
        if self.pickup_date:
            total += self.pickup_fee
        return total
    
    def save(self, *args, **kwargs):
        # Auto-calculate total if not set
        if not self.total_amount:
            self.total_amount = self.calculate_total()
        super().save(*args, **kwargs)


class PickupRequest(models.Model):
    """Separate model for pickup scheduling"""
    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name='pickup_request'
    )
    requested_pickup_date = models.DateField()
    pickup_address = models.TextField(
        blank=True,
        help_text="If different from delivery address"
    )
    pickup_notes = models.TextField(blank=True)
    
    # Payment for pickup
    stripe_payment_intent_id = models.CharField(max_length=200, blank=True)
    payment_status = models.CharField(
        max_length=20,
        default='pending',
        choices=[
            ('pending', 'Pending'),
            ('paid', 'Paid'),
            ('refunded', 'Refunded'),
        ]
    )
    
    # Notifications
    pickup_email_sent = models.BooleanField(default=False)
    pickup_sms_sent = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Pickup for {self.booking.booking_id}"
