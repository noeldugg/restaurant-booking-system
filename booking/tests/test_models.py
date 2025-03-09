from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, timedelta, time
from booking.models import Table, MenuCategory, MenuItem, Booking

class TableModelTest(TestCase):
    def setUp(self):
        self.table = Table.objects.create(number=1, capacity=4)

    def test_table_creation(self):
        self.assertEqual(str(self.table), "Table 1 (Capacity: 4)")
        self.assertEqual(self.table.capacity, 4)

class MenuModelTest(TestCase):
    def setUp(self):
        self.category = MenuCategory.objects.create(name="Main Courses")
        self.menu_item = MenuItem.objects.create(
            name="Test Dish",
            description="Test description",
            price=19.99,
            category=self.category
        )

    def test_category_creation(self):
        self.assertEqual(str(self.category), "Main Courses")

    def test_menu_item_creation(self):
        self.assertEqual(str(self.menu_item), "Test Dish")
        self.assertEqual(self.menu_item.price, 19.99)
        self.assertTrue(self.menu_item.is_available)
        self.assertEqual(self.menu_item.category, self.category)

class BookingModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', 
            email='test@example.com',
            password='testpass123'
        )
        self.table = Table.objects.create(number=5, capacity=4)
        
        # Create a booking for tomorrow
        self.tomorrow = timezone.now().date() + timedelta(days=1)
        self.booking_time = time(19, 0)  # 7:00 PM
        
        self.booking = Booking.objects.create(
            customer=self.user,
            table=self.table,
            date=self.tomorrow,
            time=self.booking_time,
            num_guests=2,
            special_requests="No nuts, please.",
            status="CONFIRMED"
        )

    def test_booking_creation(self):
        self.assertEqual(self.booking.customer, self.user)
        self.assertEqual(self.booking.table, self.table)
        self.assertEqual(self.booking.date, self.tomorrow)
        self.assertEqual(self.booking.time, self.booking_time)
        self.assertEqual(self.booking.num_guests, 2)
        self.assertEqual(self.booking.special_requests, "No nuts, please.")
        self.assertEqual(self.booking.status, "CONFIRMED")

    def test_booking_string_representation(self):
        expected_string = f"Booking for testuser on {self.tomorrow} at {self.booking_time}"
        self.assertEqual(str(self.booking), expected_string)

    def test_booking_capacity_validation(self):
        # Try to create a booking with too many guests
        with self.assertRaises(ValidationError):
            booking = Booking(
                customer=self.user,
                table=self.table,
                date=self.tomorrow,
                time=time(20, 0),  # 8:00 PM
                num_guests=6,  # Table capacity is 4
                status="PENDING"
            )
            booking.clean()

    def test_booking_past_date_validation(self):
        # Try to create a booking in the past
        yesterday = timezone.now().date() - timedelta(days=1)
        with self.assertRaises(ValidationError):
            booking = Booking(
                customer=self.user,
                table=self.table,
                date=yesterday,
                time=time(19, 0),
                num_guests=2,
                status="PENDING"
            )
            booking.clean()

    def test_booking_overlapping_validation(self):
        # Try to create another booking at the same time
        with self.assertRaises(ValidationError):
            booking = Booking(
                customer=self.user,
                table=self.table,
                date=self.tomorrow,
                time=self.booking_time,  # Same time as existing booking
                num_guests=2,
                status="PENDING"
            )
            booking.clean()
        
        # Try to create a booking that overlaps (starts during existing booking)
        with self.assertRaises(ValidationError):
            booking = Booking(
                customer=self.user,
                table=self.table,
                date=self.tomorrow,
                time=time(20, 30),  # Within 2 hours of existing 7:00 PM booking
                num_guests=2,
                status="PENDING"
            )
            booking.clean()
        
        # A booking at a different time should be valid
        booking = Booking(
            customer=self.user,
            table=self.table,
            date=self.tomorrow,
            time=time(22, 0),  # 10:00 PM (after the 2-hour slot)
            num_guests=2,
            status="PENDING"
        )
        booking.clean()  # Should not raise an exception