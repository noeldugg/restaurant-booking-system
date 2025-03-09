from django import forms
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Booking, Table

class DateInput(forms.DateInput):
    input_type = 'date'

class TimeInput(forms.TimeInput):
    input_type = 'time'

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ('date', 'time', 'num_guests', 'special_requests')
        widgets = {
            'date': DateInput(),
            'time': TimeInput(),
            'special_requests': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set minimum date to today
        self.fields['date'].widget.attrs['min'] = timezone.now().date().isoformat()
        
        # Set maximum date to 3 months from now
        max_date = timezone.now().date() + timedelta(days=90)
        self.fields['date'].widget.attrs['max'] = max_date.isoformat()
        
        # Set time constraints
        self.fields['time'].widget.attrs['min'] = '11:00'
        self.fields['time'].widget.attrs['max'] = '22:00'
        
        # Set step to 30 minutes for time field
        self.fields['time'].widget.attrs['step'] = 1800  # seconds
    
    def clean_time(self):
        time = self.cleaned_data.get('time')
        
        # Check if time is within restaurant hours (11:00 - 22:00)
        opening_time = datetime.strptime('11:00', '%H:%M').time()
        closing_time = datetime.strptime('22:00', '%H:%M').time()
        
        if time < opening_time or time > closing_time:
            raise forms.ValidationError("Bookings are only available between 11:00 AM and 10:00 PM")
        
        # Ensure time is at half-hour intervals
        if time.minute not in (0, 30):
            raise forms.ValidationError("Bookings must be at the hour or half-hour")
        
        return time
    
    def clean_num_guests(self):
        num_guests = self.cleaned_data.get('num_guests')
        
        if num_guests < 1:
            raise forms.ValidationError("Number of guests must be at least 1")
        
        if num_guests > 20:
            raise forms.ValidationError("For groups larger than 20, please contact us directly")
        
        return num_guests

class AvailabilitySearchForm(forms.Form):
    date = forms.DateField(widget=DateInput())
    time = forms.TimeField(widget=TimeInput())
    num_guests = forms.IntegerField(min_value=1, max_value=20)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set minimum date to today
        self.fields['date'].widget.attrs['min'] = timezone.now().date().isoformat()
        
        # Set time constraints
        self.fields['time'].widget.attrs['min'] = '11:00'
        self.fields['time'].widget.attrs['max'] = '22:00'