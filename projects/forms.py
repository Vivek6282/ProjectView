from django import forms
from .models import Project


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'category', 'details', 'deadline', 'status', 'priority']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter project title',
            }),
            'category': forms.Select(attrs={
                'class': 'form-select',
            }),
            'details': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Project details and description...',
                'rows': 4,
            }),
            'deadline': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'status': forms.Select(attrs={
                'class': 'form-select',
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select',
            }),
        }

    def clean_deadline(self):
        deadline = self.cleaned_data.get('deadline')
        from django.utils import timezone
        if deadline and deadline < timezone.now().date():
            raise forms.ValidationError("The deadline cannot be in the past. Please select today or a future date.")
        return deadline
