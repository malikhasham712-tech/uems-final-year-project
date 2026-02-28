from django import forms
from django.contrib.auth.models import User

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    role = forms.ChoiceField(choices=[
        ('student', 'Student'),
        ('faculty', 'Faculty'),
    ])

    class Meta:
        model = User
        fields = ['username', 'email', 'password']