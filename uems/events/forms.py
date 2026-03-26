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
            'student_name': forms.TextInput(attrs={'class': 'border rounded px-3 py-2 w-full'}),
            'registration_no': forms.TextInput(attrs={'class': 'border rounded px-3 py-2 w-full'}),
            'semester': forms.TextInput(attrs={'class': 'border rounded px-3 py-2 w-full'}),
            'department': forms.TextInput(attrs={'class': 'border rounded px-3 py-2 w-full'}),
            'email': forms.EmailInput(attrs={'class': 'border rounded px-3 py-2 w-full'}),
            'contact_no': forms.TextInput(attrs={'class': 'border rounded px-3 py-2 w-full'}),
        }