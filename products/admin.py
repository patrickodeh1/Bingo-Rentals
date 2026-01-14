from django.contrib import admin
from .models import Product, PricingSetting, BlackoutDate


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'monthly_rate', 'stock_quantity', 'is_active')
    list_filter = ('category', 'is_active', 'created_at')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'category', 'description', 'size_description')
        }),
        ('Pricing & Inventory', {
            'fields': ('monthly_rate', 'stock_quantity')
        }),
        ('Media', {
            'fields': ('image',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


@admin.register(PricingSetting)
class PricingSettingAdmin(admin.ModelAdmin):
    list_display = ('delivery_fee', 'pickup_fee', 'updated_at', 'updated_by')
    fieldsets = (
        ('Fees', {
            'fields': ('delivery_fee', 'pickup_fee')
        }),
        ('Metadata', {
            'fields': ('updated_by',),
            'classes': ('collapse',)
        }),
    )
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(BlackoutDate)
class BlackoutDateAdmin(admin.ModelAdmin):
    list_display = ('date', 'reason', 'product')
    list_filter = ('date', 'product')
    search_fields = ('reason',)
    fieldsets = (
        ('Date', {
            'fields': ('date',)
        }),
        ('Details', {
            'fields': ('reason', 'product')
        }),
    )
