from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from bookings.models import Booking, BookingStatus
from products.models import Product, PricingSetting, BlackoutDate
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
import logging

logger = logging.getLogger(__name__)


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


@staff_member_required
def dashboard_home(request):
    """Main dashboard with statistics"""
    today = timezone.now().date()

    # Statistics
    new_orders = Booking.objects.filter(
        created_at__date=today
    ).count()

    scheduled_today = Booking.objects.filter(
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

    units_available = sum(p.stock_quantity - p.active_rentals for p in products)

    # Blackout dates coming up
    upcoming_blackouts = BlackoutDate.objects.filter(
        date__gte=today
    ).order_by('date')[:3]

    # Recent orders
    recent_orders = Booking.objects.select_related('product').order_by('-created_at')[:10]

    context = {
        'new_orders': new_orders,
        'scheduled_today': scheduled_today,
        'units_available': units_available,
        'blackout_dates': upcoming_blackouts,
        'recent_orders': recent_orders,
        'page_title': 'Dashboard'
    }
    return render(request, 'dashboard/home.html', context)


@staff_member_required
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


@staff_member_required
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

    context = {
        'booking': booking,
        'status_choices': BookingStatus.choices,
        'page_title': f'Order {booking.booking_id}'
    }
    return render(request, 'dashboard/order_detail.html', context)


@staff_member_required
def manage_inventory(request):
    """Manage product inventory"""
    products = Product.objects.annotate(
        active_rentals=Count(
            'bookings',
            filter=Q(bookings__status__in=[BookingStatus.CONFIRMED, BookingStatus.IN_PROGRESS])
        )
    )

    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        stock_quantity = request.POST.get('stock_quantity')

        product = get_object_or_404(Product, id=product_id)
        product.stock_quantity = int(stock_quantity)
        product.save()

        messages.success(request, f'{product.name} stock updated to {stock_quantity}')
        return redirect('dashboard:manage_inventory')

    context = {
        'products': products,
        'page_title': 'Manage Inventory'
    }
    return render(request, 'dashboard/manage_inventory.html', context)


@staff_member_required
def pricing_settings(request):
    """Update pricing settings"""
    pricing = PricingSetting.get_settings()

    if request.method == 'POST':
        pricing.delivery_fee = request.POST.get('delivery_fee')
        pricing.pickup_fee = request.POST.get('pickup_fee')
        pricing.updated_by = request.user.username
        pricing.save()

        messages.success(request, 'Pricing updated successfully')
        return redirect('dashboard:pricing_settings')

    context = {
        'pricing': pricing,
        'page_title': 'Pricing Settings'
    }
    return render(request, 'dashboard/pricing_settings.html', context)


@staff_member_required
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


@staff_member_required
def manage_users(request):
    users = User.objects.filter(is_staff=True).order_by('username')
    return render(request, 'dashboard/manage_users.html', {'users': users, 'page_title': 'Manage Staff Users'})


@staff_member_required
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


@staff_member_required
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


@staff_member_required
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id, is_staff=True)
    if request.method == 'POST':
        user.delete()
        messages.success(request, f"Staff user deleted.")
        return redirect('dashboard:manage_users')
    return render(request, 'dashboard/delete_user.html', {'user': user, 'page_title': f'Delete {user.username}'})
