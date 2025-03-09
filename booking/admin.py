from django.contrib import admin
from .models import Table, MenuCategory, MenuItem, Booking

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ('number', 'capacity')
    search_fields = ('number',)

@admin.register(MenuCategory)
class MenuCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_available')
    list_filter = ('category', 'is_available')
    search_fields = ('name', 'description')
    list_editable = ('is_available', 'price')

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('customer', 'table', 'date', 'time', 'num_guests', 'status')
    list_filter = ('status', 'date')
    search_fields = ('customer__username', 'customer__email')
    date_hierarchy = 'date'
    list_editable = ('status',)