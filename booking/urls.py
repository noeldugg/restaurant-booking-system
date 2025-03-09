from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('menu/', views.menu, name='menu'),
    path('availability/', views.search_availability, name='search_availability'),
    path('booking/create/<int:table_id>/', views.create_booking, name='create_booking'),
    path('bookings/', views.BookingListView.as_view(), name='bookings'),
    path('booking/<int:pk>/', views.BookingDetailView.as_view(), name='booking-detail'),
    path('booking/<int:pk>/update/', views.BookingUpdateView.as_view(), name='booking-update'),
    path('booking/<int:pk>/delete/', views.BookingDeleteView.as_view(), name='booking-delete'),
    path('staff/', views.staff_dashboard, name='staff_dashboard'),
]