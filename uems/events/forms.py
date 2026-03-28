from django import forms
from .models import EventProposal, EventRegistration

class ProposalForm(forms.ModelForm):
    class Meta:
        model = EventProposal
        fields = ['proposed_venue', 'details']

class EventRegistrationForm(forms.ModelForm):
    class Meta:
        model = EventRegistration
        fields = ['student_name', 'registration_no', 'semester', 'department', 'email', 'contact_no']
        widgets = {
            'student_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Student Name'}),
            'registration_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Registration No'}),
            'semester': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Semester'}),
            'department': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Department'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'contact_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contact No'}),
        }