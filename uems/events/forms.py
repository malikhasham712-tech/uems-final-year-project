from django import forms
from .models import EventProposal, EventRegistration


# ----------------------
# PROPOSAL FORM
# ----------------------
class ProposalForm(forms.ModelForm):
    class Meta:
        model = EventProposal
        fields = ['proposed_venue', 'details']


# ----------------------
# REGISTRATION FORM (CLEAN)
# ----------------------
class EventRegistrationForm(forms.ModelForm):
    class Meta:
        model = EventRegistration
        fields = [
            'student_name',
            'registration_no',
            'semester',
            'department',
            'email',
            'contact_no'
        ]

        widgets = {
            'student_name': forms.TextInput(attrs={'class': 'form-control'}),
            'registration_no': forms.TextInput(attrs={'class': 'form-control'}),
            'semester': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'contact_no': forms.TextInput(attrs={'class': 'form-control'}),
        }