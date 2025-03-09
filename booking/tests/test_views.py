from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta, time
from booking.models import Table, Booking
import json

class HomeViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.home_url = reverse('home')

    def test_home_view_GET(self):
        response = self.client.get(self.home_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'booking/index.html')

class SearchAvailabilityViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.search_url = reverse('search_availability')
        self.user = User.objects.create_user(
            username='testuser', 
            email='test@example.com',
            password='testpass123'
        )
        self.table = Table.objects.create(number=1, capacity=4)
        
        # Create a booking for tomorrow
        self.tomorrow = timezone.now().date() + timedelta(days=1)
        self.booking_time = time(19, 0)  # 7:00 PM
        
        self.booking = Booking.objects.create(
            customer=self.user,
            table=self.table,
            date=self.tomorrow,
            time=self.booking_time,
            num_guests=2,
            status="CONFIRMED"
        )

    def test_search_availability_GET(self):
        response = self.client.get(self.search_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'booking/search_availability.html')
    
    def test_search_availability_POST_available(self):
        # Search for a time when table is available
        day_after_tomorrow = self.tomorrow + timedelta(days=1)
        
        response = self.client.post(self.search_url, {
            'date': day_after_tomorrow,
            'time': '12:00',
            'num_guests': 2
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'booking/availability_results.html')
        self.assertIn('available_tables', response.context)
        self.assertTrue(response.context['available_tables'].exists())
    
    def test_search_availability_POST_unavailable(self):
        # Search for the same time as the existing booking
        response = self.client.post(self.search_url, {
            'date': self.tomorrow,
            'time': self.booking_time,
            'num_guests': 2
        })
        
        # Should redirect to home with a message
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('home'))

class BookingCreateViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', 
            email='test@example.com',
            password='testpass123'
        )
        self.table = Table.objects.create(number=1, capacity=4)
        
        # Login the user
        self.client.login(username='testuser', password='testpass123')
        
        # URL for creating a booking
        self.create_booking_url = reverse('create_booking', args=[self.table.id])
        
        # Set up session data
        tomorrow = timezone.now().date() + timedelta(days=1)
        session = self.client.session
        session['booking_date'] = tomorrow.isoformat()
        session['booking_time'] = '19:00:00'
        session['booking_num_guests'] = 2
        session.save()

    def test_create_booking_GET(self):
        response = self.client.get(self.create_booking_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'booking/booking_form.html')
    
    def test_create_booking_POST(self):
        tomorrow = timezone.now().date() + timedelta(days=1)
        
        response = self.client.post(self.create_booking_url, {
            'date': tomorrow,
            'time': '19:00',
            'num_guests': 2,
            'special_requests': 'Test request'
        })
        
        # Should redirect to the booking detail page
        self.assertEqual(response.status_code, 302)
        
        # Check that booking was created
        booking = Booking.objects.filter(customer=self.user, table=self.table).first()
        self.assertIsNotNone(booking)
        self.assertEqual(booking.date, tomorrow)
        self.assertEqual(booking.time.strftime("%H:%M"), '19:00')
        self.assertEqual(booking.num_guests, 2)
        self.assertEqual(booking.special_requests, 'Test request')
        self.assertEqual(booking.status, 'CONFIRMED')

class BookingDetailViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', 
            email='test@example.com',
            password='testpass123'
        )
        self.table = Table.objects.create(number=1, capacity=4)
        
        # Create a booking
        self.tomorrow = timezone.now().date() + timedelta(days=1)
        self.booking = Booking.objects.create(
            customer=self.user,
            table=self.table,
            date=self.tomorrow,
            time=time(19, 0),
            num_guests=2,
            status="CONFIRMED"
        )
        
        # URL for viewing booking details
        self.detail_url = reverse('booking-detail', args=[self.booking.id])
        
        # Login the user
        self.client.login(username='testuser', password='testpass123')

    def test_booking_detail_view(self):
        response = self.client.get(self.detail_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'booking/booking_detail.html')
        self.assertEqual(response.context['booking'], self.booking)
    
    def test_booking_detail_view_unauthorized(self):
        # Create another user
        other_user = User.objects.create_user(
            username='otheruser', 
            email='other@example.com',
            password='testpass123'
        )
        
        # Login as the other user
        self.client.login(username='otheruser', password='testpass123')
        
        # Try to access the booking detail
        response = self.client.get(self.detail_url)
        
        # Should return 404 as this booking doesn't belong to the logged in user
        self.assertEqual(response.status_code, 404)

class AuthenticationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', 
            email='test@example.com',
            password='testpass123'
        )
        self.table = Table.objects.create(number=1, capacity=4)
        
        # URLs
        self.login_url = reverse('login')
        self.register_url = reverse('register')
        self.profile_url = reverse('profile')
        self.search_url = reverse('search_availability')
        
    def test_login_view(self):
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')
        
    def test_register_view(self):
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/register.html')
        
    def test_profile_view_redirect_if_not_logged_in(self):
        response = self.client.get(self.profile_url)
        self.assertRedirects(response, f'/accounts/login/?next={self.profile_url}')
        
    def test_profile_view_when_logged_in(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/profile.html')
        
    def test_search_availability_redirect_if_not_logged_in(self):
        # Search availability should be accessible without login
        response = self.client.get(self.search_url)
        self.assertEqual(response.status_code, 200)
        
        # But creating a booking should require login
        create_booking_url = reverse('create_booking', args=[self.table.id])
        response = self.client.get(create_booking_url)
        self.assertRedirects(response, f'/accounts/login/?next={create_booking_url}')