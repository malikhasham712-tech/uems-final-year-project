from django import forms
from .models import EventProposal


class ProposalForm(forms.ModelForm):

    class Meta:
        model = EventProposal
        fields = ['proposed_venue', 'details']