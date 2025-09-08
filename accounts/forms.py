from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email Address")
    full_name = forms.CharField(max_length=100, required=True, label="Full Name")
    gcash_number = forms.CharField(max_length=20, required=True, label="GCash Number")
    gcash_name = forms.CharField(max_length=100, required=True, label="GCash Name")
    bank_name = forms.CharField(max_length=100, required=True, label="Bank Name")
    bank_number = forms.CharField(max_length=30, required=True, label="Bank Number")

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "full_name",
            "password1",
            "password2",
            "gcash_number",
            "gcash_name",
            "bank_name",
            "bank_number",
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]  # save email into User model
        if commit:
            user.save()
            Profile.objects.create(
                user=user,
                full_name=self.cleaned_data["full_name"],
                gcash_number=self.cleaned_data["gcash_number"],
                gcash_name=self.cleaned_data["gcash_name"],
                bank_name=self.cleaned_data["bank_name"],
                bank_number=self.cleaned_data["bank_number"],
            )
        return user
