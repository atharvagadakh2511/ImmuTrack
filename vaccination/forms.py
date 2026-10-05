from django import forms
from django.utils import timezone
from .models import VaccineAdministrationRecord, ScheduledDose

class DoseAdministrationForm(forms.ModelForm):
    class Meta:
        model = VaccineAdministrationRecord
        fields = ['administered_date', 'batch_number', 'facility', 'clinical_notes', 'adverse_reaction', 'adverse_reaction_notes']
        widgets = {
            'administered_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'batch_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. COV-B9284-IN'}),
            'facility': forms.Select(attrs={'class': 'form-select'}),
            'clinical_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Any observations, site of injection, etc.'}),
            'adverse_reaction': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'adverse_reaction_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Details if any immediate adverse event following immunization (AEFI)'}),
        }

    def clean_administered_date(self):
        admin_date = self.cleaned_data.get('administered_date')
        if admin_date and admin_date > timezone.now().date():
            raise forms.ValidationError("Administration date cannot be in the future.")
        return admin_date
