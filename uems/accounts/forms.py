from django import forms
from django.contrib.auth.models import User

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    first_name = forms.CharField(max_length=100, required=True, label='First Name')
    last_name = forms.CharField(max_length=100, required=True, label='Last Name')
    role = forms.ChoiceField(choices=[
        ('student', 'Student'),
        ('faculty', 'Faculty'),
    ])

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password']