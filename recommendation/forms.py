from django import forms
from django.contrib.auth.models import User

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())
    full_name = forms.CharField(required=True)

    class Meta:
        model = User
        fields = ["username", "full_name", "email", "password"]

