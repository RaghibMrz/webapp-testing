from django import forms
from .models import Contact
from functools import partial


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ('subject', 'email', 'message')


# input_formats=["%Y-%m-%dT%H:%M:%S+00:00"],

DateInput = partial(forms.DateInput, {'class': 'dateinput'})


class DateRangeForm(forms.Form):
    start_date = forms.DateField(widget=DateInput())
    end_date = forms.DateField(widget=DateInput())