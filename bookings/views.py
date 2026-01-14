from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.utils import timezone
from django.contrib import messages
from django.db.models import Q
from products.models import Product, PricingSetting, BlackoutDate
from .models import Booking, PickupRequest, BookingStatus
from .forms import BookingForm, PickupRequestForm
import stripe
from django.conf import settings
import json
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY


def booking_home(request):
    """Step 1: Select Product"""
    products = Product.objects.filter(is_active=True)
    context = {
        'products': products,
        'page_title': 'Book Your Rental'
    }
    return render(request, 'booking/select_product.html', context)


def select_dates(request, product_slug):
    """Step 2: Choose Drop-off Date & Duration"""
    product = get_object_or_404(Product, slug=product_slug, is_active=True)
    pricing = PricingSetting.get_settings()
    
    # Get blackout dates for calendar
    blackout_dates = list(
        BlackoutDate.objects.filter(
            Q(product=product) | Q(product__isnull=True)
        ).values_list('date', flat=True)
    )
    
    # Convert to ISO format for JavaScript
    blackout_dates_json = json.dumps(
        [date.isoformat() for date in blackout_dates]
    )
    
    if request.method == 'POST':
        drop_off_date = request.POST.get('drop_off_date')
        rental_months = int(request.POST.get('rental_months', 1))
        
        # Store in session
        request.session['booking_data'] = {
            'product_id': product.id,
            'drop_off_date': drop_off_date,
            'rental_months': rental_months,
        }
        
        return redirect('booking:customer_details')
    
    context = {
        'product': product,
        'pricing': pricing,
        'blackout_dates': blackout_dates_json,
        'min_date': (timezone.now() + timedelta(days=1)).date().isoformat(),
        'page_title': f'Book {product.name}'
    }
    return render(request, 'booking/select_dates.html', context)


def customer_details(request):
    """Step 3: Customer Information & Location"""
    booking_data = request.session.get('booking_data')
    
    if not booking_data:
        messages.error(request, 'Please start from product selection.')
        return redirect('booking:home')
    
    product = get_object_or_404(Product, id=booking_data['product_id'])
    pricing = PricingSetting.get_settings()
    
    # Calculate pricing
    monthly_cost = product.monthly_rate * booking_data['rental_months']
    total = monthly_cost + pricing.delivery_fee
    
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            # Store customer details in session
            request.session['booking_data'].update({
                'customer_name': form.cleaned_data['customer_name'],
                'customer_email': form.cleaned_data['customer_email'],
                'customer_phone': form.cleaned_data['customer_phone'],
                'delivery_address': form.cleaned_data['delivery_address'],
                'delivery_city': form.cleaned_data['delivery_city'],
                'delivery_state': form.cleaned_data['delivery_state'],
                'delivery_zip': form.cleaned_data['delivery_zip'],
                'delivery_notes': form.cleaned_data.get('delivery_notes', ''),
            })
            
            return redirect('booking:order_summary')
    else:
        form = BookingForm()
    
    context = {
        'form': form,
        'product': product,
        'booking_data': booking_data,
        'monthly_cost': float(monthly_cost),
        'delivery_fee': float(pricing.delivery_fee),
        'total': float(total),
        'page_title': 'Your Information'
    }
    return render(request, 'booking/customer_details.html', context)


def order_summary(request):
    """Step 4: Order Summary & Payment"""
    booking_data = request.session.get('booking_data')
    
    if not booking_data or 'customer_email' not in booking_data:
        messages.error(request, 'Please complete all steps.')
        return redirect('booking:home')
    
    product = get_object_or_404(Product, id=booking_data['product_id'])
    pricing = PricingSetting.get_settings()
    
    # Calculate pricing
    monthly_cost = float(product.monthly_rate) * booking_data['rental_months']
    total = monthly_cost + float(pricing.delivery_fee)
    
    # Create Stripe PaymentIntent
    try:
        intent = stripe.PaymentIntent.create(
            amount=int(total * 100),  # Stripe uses cents
            currency='usd',
            metadata={
                'product_name': product.name,
                'customer_email': booking_data['customer_email'],
                'drop_off_date': booking_data['drop_off_date'],
            }
        )
        
        client_secret = intent.client_secret
        intent_id = intent.id
    except Exception as e:
        logger.error(f'Stripe PaymentIntent creation error: {str(e)}')
        messages.error(request, f'Payment setup error: {str(e)}')
        return redirect('booking:customer_details')
    
    context = {
        'product': product,
        'booking_data': booking_data,
        'monthly_cost': monthly_cost,
        'delivery_fee': float(pricing.delivery_fee),
        'total': total,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
        'client_secret': client_secret,
        'intent_id': intent_id,
        'page_title': 'Order Summary & Payment'
    }
    return render(request, 'booking/order_summary.html', context)


@require_http_methods(["POST"])
def process_payment(request):
    """Process payment and create booking"""
    booking_data = request.session.get('booking_data')
    
    if not booking_data:
        return JsonResponse({'error': 'Session expired'}, status=400)
    
    try:
        payment_intent_id = request.POST.get('payment_intent_id')
        
        # Verify payment with Stripe
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        
        if intent.status != 'succeeded':
            return JsonResponse({'error': 'Payment not completed'}, status=400)
        
        # Create booking
        product = Product.objects.get(id=booking_data['product_id'])
        pricing = PricingSetting.get_settings()
        
        booking = Booking.objects.create(
            product=product,
            customer_name=booking_data['customer_name'],
            customer_email=booking_data['customer_email'],
            customer_phone=booking_data['customer_phone'],
            delivery_address=booking_data['delivery_address'],
            delivery_city=booking_data['delivery_city'],
            delivery_state=booking_data['delivery_state'],
            delivery_zip=booking_data['delivery_zip'],
            delivery_notes=booking_data.get('delivery_notes', ''),
            drop_off_date=booking_data['drop_off_date'],
            rental_months=booking_data['rental_months'],
            monthly_rate=product.monthly_rate,
            delivery_fee=pricing.delivery_fee,
            pickup_fee=pricing.pickup_fee,
            stripe_payment_intent_id=payment_intent_id,
            stripe_charge_id=intent.charges.data[0].id if intent.charges.data else '',
            payment_status='paid',
            status=BookingStatus.CONFIRMED,
            confirmed_at=timezone.now()
        )
        
        # Clear session
        del request.session['booking_data']
        
        # Send notifications (async)
        from notifications.tasks import send_booking_confirmation
        send_booking_confirmation(booking.id)
        
        return JsonResponse({
            'success': True,
            'booking_id': str(booking.booking_id),
            'redirect_url': f'/booking/confirmation/{booking.booking_id}/'
        })
        
    except Exception as e:
        logger.error(f'Payment processing error: {str(e)}')
        return JsonResponse({'error': str(e)}, status=500)


def booking_confirmation(request, booking_id):
    """Confirmation page after successful booking"""
    booking = get_object_or_404(Booking, booking_id=booking_id)
    
    context = {
        'booking': booking,
        'page_title': 'Booking Confirmed'
    }
    return render(request, 'booking/confirmation.html', context)


def schedule_pickup(request):
    """Guest pickup scheduling form"""
    if request.method == 'POST':
        form = PickupRequestForm(request.POST)
        if form.is_valid():
            booking_id = form.cleaned_data['booking_id']
            customer_email = form.cleaned_data['customer_email']
            
            # Verify booking exists and email matches
            try:
                booking = Booking.objects.get(
                    booking_id=booking_id,
                    customer_email=customer_email,
                    status__in=[BookingStatus.CONFIRMED, BookingStatus.IN_PROGRESS]
                )
            except Booking.DoesNotExist:
                messages.error(request, 'Booking not found or invalid email.')
                return render(request, 'booking/schedule_pickup.html', {'form': form})
            
            # Check if pickup already scheduled
            if hasattr(booking, 'pickup_request'):
                messages.info(request, 'Pickup already scheduled for this booking.')
                return redirect('booking:pickup_detail', booking_id=booking_id)
            
            # Store in session for payment
            request.session['pickup_data'] = {
                'booking_id': str(booking_id),
                'requested_pickup_date': form.cleaned_data['requested_pickup_date'].isoformat(),
                'pickup_notes': form.cleaned_data.get('pickup_notes', ''),
            }
            
            return redirect('booking:pickup_payment')
    else:
        form = PickupRequestForm()
    
    context = {
        'form': form,
        'page_title': 'Schedule Pickup'
    }
    return render(request, 'booking/schedule_pickup.html', context)


def pickup_payment(request):
    """Pickup payment processing"""
    pickup_data = request.session.get('pickup_data')
    
    if not pickup_data:
        messages.error(request, 'Please complete the pickup form first.')
        return redirect('booking:schedule_pickup')
    
    booking = get_object_or_404(Booking, booking_id=pickup_data['booking_id'])
    pricing = PricingSetting.get_settings()
    
    # Create Stripe PaymentIntent for pickup fee
    try:
        intent = stripe.PaymentIntent.create(
            amount=int(float(pricing.pickup_fee) * 100),
            currency='usd',
            metadata={
                'booking_id': str(booking.booking_id),
                'type': 'pickup_fee',
            }
        )
        
        client_secret = intent.client_secret
    except Exception as e:
        logger.error(f'Stripe PaymentIntent creation error for pickup: {str(e)}')
        messages.error(request, f'Payment setup error: {str(e)}')
        return redirect('booking:schedule_pickup')
    
    context = {
        'booking': booking,
        'pickup_data': pickup_data,
        'pickup_fee': float(pricing.pickup_fee),
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
        'client_secret': client_secret,
        'intent_id': intent.id,
        'page_title': 'Pickup Payment'
    }
    return render(request, 'booking/pickup_payment.html', context)


@require_http_methods(["POST"])
def process_pickup(request):
    """Process pickup payment and create pickup request"""
    pickup_data = request.session.get('pickup_data')
    
    if not pickup_data:
        return JsonResponse({'error': 'Session expired'}, status=400)
    
    try:
        payment_intent_id = request.POST.get('payment_intent_id')
        
        # Verify payment
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        
        if intent.status != 'succeeded':
            return JsonResponse({'error': 'Payment not completed'}, status=400)
        
        # Create pickup request
        booking = Booking.objects.get(booking_id=pickup_data['booking_id'])
        
        pickup_request = PickupRequest.objects.create(
            booking=booking,
            requested_pickup_date=pickup_data['requested_pickup_date'],
            pickup_notes=pickup_data.get('pickup_notes', ''),
            stripe_payment_intent_id=payment_intent_id,
            payment_status='paid',
            confirmed_at=timezone.now()
        )
        
        # Update booking
        booking.status = BookingStatus.PICKUP_SCHEDULED
        booking.pickup_date = pickup_data['requested_pickup_date']
        booking.save()
        
        # Clear session
        del request.session['pickup_data']
        
        # Send notifications
        from notifications.tasks import send_pickup_confirmation
        send_pickup_confirmation(pickup_request.id)
        
        return JsonResponse({
            'success': True,
            'booking_id': str(booking.booking_id),
            'redirect_url': f'/booking/pickup/confirmed/{booking.booking_id}/'
        })
        
    except Exception as e:
        logger.error(f'Pickup processing error: {str(e)}')
        return JsonResponse({'error': str(e)}, status=500)


def pickup_confirmed(request, booking_id):
    """Pickup confirmation page"""
    booking = get_object_or_404(Booking, booking_id=booking_id)
    
    context = {
        'booking': booking,
        'page_title': 'Pickup Confirmed'
    }
    return render(request, 'booking/pickup_confirmed.html', context)

