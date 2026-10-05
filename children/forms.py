from django import forms
from django.utils import timezone
from .models import Child
from accounts.models import Clinic

class ChildRegistrationForm(forms.ModelForm):
    class Meta:
        model = Child
        fields = ['first_name', 'last_name', 'date_of_birth', 'gender', 'blood_group', 'guardian_relationship', 'assigned_clinic', 'allergies']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Child first name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Child last name'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'blood_group': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. B+, O+'}),
            'guardian_relationship': forms.Select(attrs={'class': 'form-select'}),
            'assigned_clinic': forms.Select(attrs={'class': 'form-select'}),
            'allergies': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Any documented drug/food allergies'}),
        }

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob and dob > timezone.now().date():
            raise forms.ValidationError("Date of birth cannot be in the future.")
        return dob
