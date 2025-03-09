from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, DeleteView
from django.views.generic.edit import CreateView, UpdateView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta

from .models import Booking, Table, MenuItem, MenuCategory
from .forms import BookingForm, AvailabilitySearchForm

def home(request):
    """Home page view"""
    # Get upcoming featured bookings
    current_datetime = timezone.now()
    featured_tables = Table.objects.filter(capacity__gte=4)[:3]
    
    # For the search form
    form = AvailabilitySearchForm()
    
    context = {
        'featured_tables': featured_tables,
        'form': form,
    }
    
    return render(request, 'booking/index.html', context)

def menu(request):
    """Menu page view"""
    categories = MenuCategory.objects.all()
    
    context = {
        'categories': categories,
    }
    
    return render(request, 'booking/menu.html', context)

@login_required
def search_availability(request):
    """Search for available tables"""
    if request.method == 'POST':
        form = AvailabilitySearchForm(request.POST)
        if form.is_valid():
            date = form.cleaned_data['date']
            time = form.cleaned_data['time']
            num_guests = form.cleaned_data['num_guests']
            
            # Find tables with sufficient capacity
            suitable_tables = Table.objects.filter(capacity__gte=num_guests)
            
            # Check which tables are not booked at the requested time
            booking_datetime = datetime.combine(date, time)
            booking_end_time = (booking_datetime + timedelta(hours=2)).time()
            
            # Get all bookings for the date
            existing_bookings = Booking.objects.filter(
                date=date,
                table__in=suitable_tables,
                status__in=['PENDING', 'CONFIRMED']
            )
            
            # Filter out tables with overlapping bookings
            booked_tables = []
            for booking in existing_bookings:
                booking_end = (datetime.combine(datetime.today(), booking.time) + 
                              timedelta(hours=2)).time()
                
                if (time <= booking.time < booking_end_time or 
                    time < booking_end <= booking_end_time or
                    (booking.time <= time and booking_end >= booking_end_time)):
                    booked_tables.append(booking.table.id)
            
            available_tables = suitable_tables.exclude(id__in=booked_tables)
            
            if available_tables.exists():
                # Store search criteria in session for booking creation
                request.session['booking_date'] = date.isoformat()
                request.session['booking_time'] = time.isoformat()
                request.session['booking_num_guests'] = num_guests
                
                context = {
                    'date': date,
                    'time': time,
                    'num_guests': num_guests,
                    'available_tables': available_tables,
                }
                
                return render(request, 'booking/availability_results.html', context)
            else:
                messages.warning(request, "No tables available for the selected criteria.")
                return redirect('home')
    else:
        form = AvailabilitySearchForm()
    
    return render(request, 'booking/search_availability.html', {'form': form})

@login_required
def create_booking(request, table_id):
    """Create a booking for a specific table"""
    table = get_object_or_404(Table, id=table_id)
    
    # Retrieve search criteria from session
    try:
        date = datetime.fromisoformat(request.session.get('booking_date'))
        time = datetime.fromisoformat(request.session.get('booking_time')).time()
        num_guests = request.session.get('booking_num_guests')
    except (ValueError, TypeError):
        messages.error(request, "Session data is missing. Please search for availability again.")
        return redirect('search_availability')
    
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.customer = request.user
            booking.table = table
            booking.status = 'CONFIRMED'  # Auto-confirm for now
            
            try:
                booking.save()
                messages.success(request, "Booking confirmed successfully!")
                
                # Clear session data
                request.session.pop('booking_date', None)
                request.session.pop('booking_time', None)
                request.session.pop('booking_num_guests', None)
                
                return redirect('booking-detail', pk=booking.pk)
            except Exception as e:
                messages.error(request, f"Error creating booking: {str(e)}")
    else:
        # Pre-fill form with session data
        initial_data = {
            'date': date,
            'time': time,
            'num_guests': num_guests,
        }
        form = BookingForm(initial=initial_data)
    
    context = {
        'form': form,
        'table': table,
        'date': date,
        'time': time,
        'num_guests': num_guests,
    }
    
    return render(request, 'booking/booking_form.html', context)

class BookingListView(LoginRequiredMixin, ListView):
    """View to list all bookings for the current user"""
    model = Booking
    template_name = 'booking/booking_list.html'
    context_object_name = 'bookings'
    
    def get_queryset(self):
        # Filter bookings for the current user
        return Booking.objects.filter(customer=self.request.user)

class BookingDetailView(LoginRequiredMixin, DetailView):
    """View to display a booking's details"""
    model = Booking
    template_name = 'booking/booking_detail.html'
    
    def get_queryset(self):
        # Ensure users can only view their own bookings
        if self.request.user.profile.is_staff:
            return Booking.objects.all()
        return Booking.objects.filter(customer=self.request.user)

class BookingUpdateView(LoginRequiredMixin, UpdateView):
    """View to update a booking"""
    model = Booking
    form_class = BookingForm
    template_name = 'booking/booking_form.html'
    
    def get_queryset(self):
        # Ensure users can only update their own bookings
        if self.request.user.profile.is_staff:
            return Booking.objects.all()
        return Booking.objects.filter(customer=self.request.user)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Booking updated successfully!")
        return response

class BookingDeleteView(LoginRequiredMixin, DeleteView):
    """View to delete a booking"""
    model = Booking
    template_name = 'booking/booking_confirm_delete.html'
    success_url = reverse_lazy('bookings')
    
    def get_queryset(self):
        # Ensure users can only delete their own bookings
        if self.request.user.profile.is_staff:
            return Booking.objects.all()
        return Booking.objects.filter(customer=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Booking cancelled successfully!")
        return super().delete(request, *args, **kwargs)

# Staff views
@login_required
def staff_dashboard(request):
    """Dashboard for staff members"""
    # Check if user is staff
    if not request.user.profile.is_staff:
        messages.error(request, "You do not have permission to access this page.")
        return redirect('home')
    
    # Get today's bookings
    today = timezone.now().date()
    todays_bookings = Booking.objects.filter(
        date=today, 
        status__in=['CONFIRMED', 'PENDING']
    ).order_by('time')
    
    # Get upcoming bookings (next 7 days)
    end_date = today + timedelta(days=7)
    upcoming_bookings = Booking.objects.filter(
        date__gt=today,
        date__lte=end_date,
        status__in=['CONFIRMED', 'PENDING']
    ).order_by('date', 'time')
    
    context = {
        'todays_bookings': todays_bookings,
        'upcoming_bookings': upcoming_bookings,
    }
    
    return render(request, 'booking/staff_dashboard.html', context)