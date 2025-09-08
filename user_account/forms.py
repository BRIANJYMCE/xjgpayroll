from django.contrib.auth.models import User
from django import forms
from .models import TimeLog
from accounts.models import Profile 

class TimeLogForm(forms.ModelForm):
    class Meta:
        model = TimeLog
        fields = ['work_type', 'notes']  # only these fields
        widgets = {
            'work_type': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg',
                'rows': 2
            }),
        }


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "email"]

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["full_name", "gcash_number", "gcash_name", "bank_name", "bank_number"]
