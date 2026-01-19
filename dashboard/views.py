from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from bookings.models import Booking, BookingStatus
from products.models import Product, PricingSetting, BlackoutDate, DistanceBasedFee
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
import logging

logger = logging.getLogger(__name__)


# Custom decorator to require staff access
def staff_required(view_func):
    """Decorator that requires user to be staff"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('booking:staff_login')
        if not request.user.is_staff:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper



class StaffUserForm(UserCreationForm):
    email = forms.EmailField(required=True)
    is_staff = forms.BooleanField(initial=True, required=False)
    is_superuser = forms.BooleanField(initial=False, required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'is_staff', 'is_superuser')


class StaffUserEditForm(UserChangeForm):
    password = None
    email = forms.EmailField(required=True)
    is_staff = forms.BooleanField(required=False)
    is_superuser = forms.BooleanField(required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'is_staff', 'is_superuser')


@staff_required
def dashboard_home(request):
    """Main dashboard with statistics"""
    today = timezone.now().date()

    # Statistics
    new_orders_count = Booking.objects.filter(
        created_at__date=today
    ).count()

    scheduled_today_count = Booking.objects.filter(
        drop_off_date=today,
        status=BookingStatus.CONFIRMED
    ).count()

    # Units available (total stock - active rentals)
    products = Product.objects.annotate(
        active_rentals=Count(
            'bookings',
            filter=Q(
                bookings__status__in=[BookingStatus.CONFIRMED, BookingStatus.IN_PROGRESS],
                bookings__drop_off_date__lte=today,
                bookings__pickup_date__gte=today
            ) | Q(
                bookings__status__in=[BookingStatus.CONFIRMED, BookingStatus.IN_PROGRESS],
                bookings__drop_off_date__lte=today,
                bookings__pickup_date__isnull=True
            )
        )
    )

    total_available = sum(p.stock_quantity - p.active_rentals for p in products)

    # Blackout dates coming up
    blackout_dates = BlackoutDate.objects.filter(
        date__gte=today
    ).order_by('date')[:3]

    upcoming_blackouts_count = BlackoutDate.objects.filter(
        date__gte=today
    ).count()

    # Recent orders
    recent_orders = Booking.objects.select_related('product').order_by('-created_at')[:10]

    context = {
        'new_orders_count': new_orders_count,
        'scheduled_today_count': scheduled_today_count,
        'total_available': total_available,
        'blackout_dates': blackout_dates,
        'upcoming_blackouts_count': upcoming_blackouts_count,
        'products': products,
        'recent_orders': recent_orders,
        'page_title': 'Dashboard'
    }
    return render(request, 'dashboard/home.html', context)


@staff_required
def manage_orders(request):
    """View and manage all orders"""
    status_filter = request.GET.get('status', 'all')
    date_filter = request.GET.get('date', 'all')

    orders = Booking.objects.select_related('product').order_by('-created_at')

    # Apply filters
    if status_filter != 'all':
        orders = orders.filter(status=status_filter)

    if date_filter == 'today':
        orders = orders.filter(drop_off_date=timezone.now().date())
    elif date_filter == 'week':
        week_start = timezone.now().date()
        week_end = week_start + timedelta(days=7)
        orders = orders.filter(drop_off_date__range=[week_start, week_end])

    context = {
        'orders': orders,
        'status_filter': status_filter,
        'date_filter': date_filter,
        'status_choices': BookingStatus.choices,
        'page_title': 'Manage Orders'
    }
    return render(request, 'dashboard/manage_orders.html', context)


@staff_required
def order_detail(request, booking_id):
    """View single order details"""
    booking = get_object_or_404(
        Booking.objects.select_related('product'),
        booking_id=booking_id
    )

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_status':
            new_status = request.POST.get('status')
            booking.status = new_status
            booking.save()
            messages.success(request, f'Order status updated to {booking.get_status_display()}')
            return redirect('dashboard:order_detail', booking_id=booking_id)

    # Calculate monthly cost
    monthly_cost = booking.monthly_rate * booking.rental_months
    
    context = {
        'booking': booking,
        'monthly_cost': monthly_cost,
        'status_choices': BookingStatus.choices,
        'page_title': f'Order {booking.booking_id}'
    }
    return render(request, 'dashboard/order_detail.html', context)


@staff_required
def manage_inventory(request):
    """Manage product inventory"""
    products = Product.objects.annotate(
        active_rentals=Count(
            'bookings',
            filter=Q(bookings__status__in=[BookingStatus.CONFIRMED, BookingStatus.IN_PROGRESS])
        )
    )

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'create':
            name = request.POST.get('name')
            category = request.POST.get('category')
            description = request.POST.get('description')
            size_description = request.POST.get('size_description')
            monthly_rate = request.POST.get('monthly_rate')
            stock_quantity = request.POST.get('stock_quantity', 0)
            image_file = request.FILES.get('image')
            
            try:
                product = Product.objects.create(
                    name=name,
                    category=category,
                    description=description,
                    size_description=size_description,
                    monthly_rate=monthly_rate,
                    stock_quantity=int(stock_quantity),
                    is_active=True
                )
                
                if image_file:
                    product.image = image_file
                    product.save()
                
                messages.success(request, f'Product "{name}" created successfully!')
            except Exception as e:
                messages.error(request, f'Error creating product: {str(e)}')
        
        return redirect('dashboard:manage_inventory')

    context = {
        'products': products,
        'categories': Product._meta.get_field('category').choices,
        'page_title': 'Manage Inventory'
    }
    return render(request, 'dashboard/manage_inventory.html', context)


@staff_required
def edit_product(request, product_id):
    """Edit product details"""
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        # Update product details
        product.name = request.POST.get('name', product.name)
        product.category = request.POST.get('category', product.category)
        product.description = request.POST.get('description', product.description)
        product.size_description = request.POST.get('size_description', product.size_description)
        product.monthly_rate = request.POST.get('monthly_rate', product.monthly_rate)
        product.stock_quantity = request.POST.get('stock_quantity', product.stock_quantity)
        
        # Update image if provided
        if request.FILES.get('image'):
            product.image = request.FILES.get('image')
        
        product.save()
        messages.success(request, f'Product "{product.name}" updated successfully!')
        return redirect('dashboard:manage_inventory')
    
    context = {
        'product': product,
        'categories': Product._meta.get_field('category').choices,
        'page_title': f'Edit {product.name}'
    }
    return render(request, 'dashboard/edit_product.html', context)


@staff_required
def delete_product(request, product_id):
    """Delete a product listing"""
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Product "{product_name}" has been deleted successfully!')
        return redirect('dashboard:manage_inventory')
    
    context = {
        'product': product,
        'page_title': f'Delete {product.name}'
    }
    return render(request, 'dashboard/delete_product.html', context)


@staff_required
def pricing_settings(request):
    """Update pricing settings and distance-based fees"""
    pricing = PricingSetting.get_settings()
    distance_fees = DistanceBasedFee.objects.all().order_by('min_distance_km')

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_transport_fee':
            pricing.transport_fee = request.POST.get('transport_fee')
            pricing.updated_by = request.user.username
            pricing.save()
            messages.success(request, 'Pricing updated successfully')
        
        elif action == 'update_distance_fee':
            fee_id = request.POST.get('fee_id')
            fee = DistanceBasedFee.objects.get(id=fee_id)
            fee.fee = request.POST.get('fee')
            fee.description = request.POST.get('description')
            fee.is_active = request.POST.get('is_active') == 'on'
            fee.save()
            messages.success(request, f'Distance fee updated: {fee.description}')
        
        elif action == 'add_distance_fee':
            try:
                DistanceBasedFee.objects.create(
                    min_distance_km=request.POST.get('min_distance_km'),
                    max_distance_km=request.POST.get('max_distance_km'),
                    fee=request.POST.get('fee'),
                    description=request.POST.get('description'),
                    is_active=True
                )
                messages.success(request, 'New distance fee tier added')
            except Exception as e:
                messages.error(request, f'Error adding distance fee: {str(e)}')
        
        return redirect('dashboard:pricing_settings')

    context = {
        'pricing': pricing,
        'distance_fees': distance_fees,
        'page_title': 'Pricing Settings'
    }
    return render(request, 'dashboard/pricing_settings.html', context)


@staff_required
def manage_blackouts(request):
    """Manage blackout dates"""
    blackouts = BlackoutDate.objects.select_related('product').order_by('-date')
    products = Product.objects.all()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
            date = request.POST.get('date')
            reason = request.POST.get('reason')
            product_id = request.POST.get('product_id')

            product = None
            if product_id:
                product = Product.objects.get(id=product_id)

            BlackoutDate.objects.create(
                date=date,
                reason=reason,
                product=product
            )
            messages.success(request, 'Blackout date added')

        elif action == 'delete':
            blackout_id = request.POST.get('blackout_id')
            BlackoutDate.objects.filter(id=blackout_id).delete()
            messages.success(request, 'Blackout date removed')

        return redirect('dashboard:manage_blackouts')

    context = {
        'blackouts': blackouts,
        'products': products,
        'page_title': 'Blackout Dates'
    }
    return render(request, 'dashboard/manage_blackouts.html', context)


@staff_required
def manage_users(request):
    users = User.objects.filter(is_staff=True).order_by('username')
    return render(request, 'dashboard/manage_users.html', {'users': users, 'page_title': 'Manage Staff Users'})


@staff_required
def create_user(request):
    if request.method == 'POST':
        form = StaffUserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_staff = form.cleaned_data['is_staff']
            user.is_superuser = form.cleaned_data['is_superuser']
            user.save()
            messages.success(request, f"Staff user '{user.username}' created.")
            return redirect('dashboard:manage_users')
    else:
        form = StaffUserForm()
    return render(request, 'dashboard/create_user.html', {'form': form, 'page_title': 'Create Staff User'})


@staff_required
def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id, is_staff=True)
    if request.method == 'POST':
        form = StaffUserEditForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_staff = form.cleaned_data['is_staff']
            user.is_superuser = form.cleaned_data['is_superuser']
            user.save()
            messages.success(request, f"Staff user '{user.username}' updated.")
            return redirect('dashboard:manage_users')
    else:
        form = StaffUserEditForm(instance=user)
    return render(request, 'dashboard/edit_user.html', {'form': form, 'user': user, 'page_title': f'Edit {user.username}'})


@staff_required
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id, is_staff=True)
    if request.method == 'POST':
        user.delete()
        messages.success(request, f"Staff user deleted.")
        return redirect('dashboard:manage_users')
    return render(request, 'dashboard/delete_user.html', {'user': user, 'page_title': f'Delete {user.username}'})


@staff_required
def payment_history(request):
    """View payment and order history"""
    status_filter = request.GET.get('status', 'all')
    
    orders = Booking.objects.select_related('product').order_by('-created_at')
    
    # Apply filters
    if status_filter != 'all':
        orders = orders.filter(status=status_filter)
    
    # Calculate totals
    total_revenue = sum(order.total_amount for order in orders)
    active_bookings_count = orders.filter(status=BookingStatus.CONFIRMED).count()
    
    context = {
        'orders': orders,
        'status_filter': status_filter,
        'status_choices': BookingStatus.choices,
        'total_revenue': total_revenue,
        'active_bookings_count': active_bookings_count,
        'page_title': 'Payment History'
    }
    return render(request, 'dashboard/payment_history.html', context)
