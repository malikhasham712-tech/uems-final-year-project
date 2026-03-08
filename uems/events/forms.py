from django import forms
from .models import EventProposal

class EventProposalForm(forms.ModelForm):
    class Meta:
        model = EventProposal
        fields = ['event_name', 'description', 'proposed_venue']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }