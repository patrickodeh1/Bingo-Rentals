from django.db import models
from django.core.validators import MinValueValidator
from django.utils.text import slugify
from cloudinary.models import CloudinaryField


class ProductCategory(models.TextChoices):
    STORAGE_POD = 'storage_pod', 'Storage Pod'
    GARBAGE_BIN = 'garbage_bin', 'Garbage Bin'


class Product(models.Model):
    """Rental products: Storage Pods and Garbage Bins"""
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    category = models.CharField(
        max_length=20,
        choices=ProductCategory.choices
    )
    description = models.TextField()
    size_description = models.CharField(
        max_length=100,
        help_text="e.g., '8ft or 16ft Units' or '10-Yard Dumpster'"
    )
    monthly_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = CloudinaryField('image', folder='bingo-rentals/products')
    stock_quantity = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Total available units"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            # Handle duplicate slugs
            original_slug = self.slug
            counter = 1
            while Product.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)
    
    def get_available_quantity(self, date):
        """Calculate available quantity for a specific date"""
        from bookings.models import Booking
        booked = Booking.objects.filter(
            product=self,
            status__in=['confirmed', 'in_progress'],
            drop_off_date__lte=date,
            pickup_date__gte=date
        ).count()
        return self.stock_quantity - booked


class PricingSetting(models.Model):
    """Global pricing settings"""
    transport_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=80.00,
        help_text="Flat fee for delivery and removal (covers both)"
    )
    delivery_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=79.00,
        blank=True,
        null=True,
        help_text="Legacy - use transport_fee instead"
    )
    pickup_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=79.00,
        blank=True,
        null=True,
        help_text="Legacy - use transport_fee instead"
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.CharField(max_length=100, blank=True)
    
    class Meta:
        verbose_name = "Pricing Setting"
        verbose_name_plural = "Pricing Settings"
    
    def __str__(self):
        return f"Transport Fee: ${self.transport_fee}"
    
    @classmethod
    def get_settings(cls):
        """Get or create pricing settings"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class BlackoutDate(models.Model):
    """Dates when bookings are not allowed"""
    date = models.DateField(unique=True)
    reason = models.CharField(max_length=200)
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Leave blank to apply to all products"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['date']
    
    def __str__(self):
        return f"{self.date} - {self.reason}"
